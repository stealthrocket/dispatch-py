#include <assert.h>
#include <stdbool.h>
#include <stdio.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#if PY_MAJOR_VERSION != 3 || (PY_MINOR_VERSION < 11 || PY_MINOR_VERSION > 13)
# error Python 3.11-3.13 is required
#endif

// This is a redefinition of the private/opaque struct _PyInterpreterFrame:
// https://github.com/python/cpython/blob/3.12/Include/cpython/pyframe.h#L23
// https://github.com/python/cpython/blob/3.12/Include/internal/pycore_frame.h#L51
typedef struct InterpreterFrame {
#if PY_MINOR_VERSION == 11
    PyFunctionObject *f_func;
#elif PY_MINOR_VERSION >= 12
    PyCodeObject *f_code; // 3.13: PyObject *f_executable
    struct _PyInterpreterFrame *previous;
    PyObject *f_funcobj;
#endif
    PyObject *f_globals;
    PyObject *f_builtins;
    PyObject *f_locals;
#if PY_MINOR_VERSION == 11
    PyCodeObject *f_code;
    PyFrameObject *frame_obj;
    struct _PyInterpreterFrame *previous;
    _Py_CODEUNIT *prev_instr;
    int stacktop;
    bool is_entry;
#elif PY_MINOR_VERSION >= 12
    PyFrameObject *frame_obj;
    _Py_CODEUNIT *prev_instr; // 3.13: _Py_CODEUNIT *instr_ptr
    int stacktop;
    uint16_t return_offset;
#endif
    char owner;
    PyObject *localsplus[1];
} InterpreterFrame;

// This is a redefinition of the private/opaque PyFrameObject:
// https://github.com/python/cpython/blob/3.12/Include/pytypedefs.h#L22
// https://github.com/python/cpython/blob/3.12/Include/internal/pycore_frame.h#L16
// The definition is the same for Python 3.11-3.13.
typedef struct FrameObject {
    PyObject_HEAD
    PyFrameObject *f_back;
    struct _PyInterpreterFrame *f_frame;
    PyObject *f_trace;
    int f_lineno;
    char f_trace_lines;
    char f_trace_opcodes;
    char f_fast_as_locals;
    PyObject *_f_frame_data[1];
} FrameObject;

// This is a redefinition of frame state constants:
// https://github.com/python/cpython/blob/3.12/Include/internal/pycore_frame.h#L34
// The definition is the same for Python 3.11 and 3.12.
// XXX: note that these constants change in 3.13!
typedef enum _framestate {
#if PY_MINOR_VERSION == 13
    FRAME_CREATED = -3,
    FRAME_SUSPENDED = -2,
    FRAME_SUSPENDED_YIELD_FROM = -1,
#else
    FRAME_CREATED = -2,
    FRAME_SUSPENDED = -1,
#endif
    FRAME_EXECUTING = 0,
    FRAME_COMPLETED = 1,
    FRAME_CLEARED = 4
} FrameState;

// For reference, PyGenObject is defined as follows after expanding top-most macro:
// https://github.com/python/cpython/blob/3.12/Include/cpython/genobject.h
/*
typedef struct {
    PyObject_HEAD
#if PY_MINOR_VERSION == 11
    PyCodeObject *gi_code;
#endif
    PyObject *gi_weakreflist;
    PyObject *gi_name;
    PyObject *gi_qualname;
    _PyErr_StackItem gi_exc_state;
    PyObject *gi_origin_or_finalizer;
    char gi_hooks_inited;
    char gi_closed;
    char gi_running_async;
    int8_t gi_frame_state;
    PyObject *gi_iframe[1];
} PyGenObject;
*/

static InterpreterFrame *get_interpreter_frame(PyObject *obj) {
    struct _PyInterpreterFrame *frame = NULL;
    if (PyGen_Check(obj)) {
        PyGenObject *gen_obj = (PyGenObject *)obj;
        frame = (struct _PyInterpreterFrame *)(gen_obj->gi_iframe);
    } else if (PyFrame_Check(obj)) {
        PyFrameObject *frame_obj = (PyFrameObject *)obj;
        frame = ((FrameObject *)frame_obj)->f_frame;
    } else {
        PyErr_SetString(PyExc_TypeError, "Object is not a generator or frame");
        return NULL;
    }
    assert(frame);
    return (InterpreterFrame *)frame;
}

static InterpreterFrame *get_interpreter_frame_from_args(PyObject *args) {
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }
    return get_interpreter_frame(obj);
}

static PyGenObject *get_generator_from_args(PyObject *args) {
    PyObject *gen_arg;
    if (!PyArg_ParseTuple(args, "O", &gen_arg)) {
        return NULL;
    }
    if (!PyGen_Check(gen_arg)) {
        PyErr_SetString(PyExc_TypeError, "Input object is not a generator");
        return NULL;
    }
    return (PyGenObject *)gen_arg;
}

static PyObject *get_generator_frame_state(PyObject *self, PyObject *args) {
    PyGenObject *gen = get_generator_from_args(args);
    if (!gen) {
        return NULL;
    }
    return PyLong_FromLong((long)gen->gi_frame_state);
}

static PyObject *get_frame_ip(PyObject *self, PyObject *args) {
    // Note that this method is redundant. You can access the instruction pointer via g.gi_frame.f_lasti.
    InterpreterFrame *frame = get_interpreter_frame_from_args(args);
    if (!frame) {
        return NULL;
    }
    assert(frame->f_code);
    assert(frame->prev_instr);
    // See _PyInterpreterFrame_LASTI
    // https://github.com/python/cpython/blob/3.12/Include/internal/pycore_frame.h#L77
    intptr_t ip = (intptr_t)frame->prev_instr - (intptr_t)_PyCode_CODE(frame->f_code);
    return PyLong_FromLong((long)ip);
}

static PyObject *get_frame_sp(PyObject *self, PyObject *args) {
    InterpreterFrame *frame = get_interpreter_frame_from_args(args);
    if (!frame) {
        return NULL;
    }
    assert(frame->stacktop >= 0);
    int sp = frame->stacktop;
    return PyLong_FromLong((long)sp);
}

static PyObject *get_frame_stack_at(PyObject *self, PyObject *args) {
    PyObject *frame_obj;
    int index;
    if (!PyArg_ParseTuple(args, "Oi", &frame_obj, &index)) {
        return NULL;
    }
    InterpreterFrame *frame = get_interpreter_frame(frame_obj);
    if (!frame) {
        return NULL;
    }
    assert(frame->stacktop >= 0);

    int limit = frame->f_code->co_stacksize + frame->f_code->co_nlocalsplus;
    if (index < 0 || index >= limit) {
        PyErr_SetString(PyExc_IndexError, "Index out of bounds");
        return NULL;
    }

    // NULL in C != None in Python. We need to preserve the fact that some items
    // on the stack are NULL (not yet available).
    PyObject *is_null = Py_False;
    PyObject *obj = frame->localsplus[index];
    if (!obj) {
        is_null = Py_True;
        obj = Py_None;
    }
    return PyTuple_Pack(2, is_null, obj);
}

static PyObject *set_frame_ip(PyObject *self, PyObject *args) {
    PyObject *frame_obj;
    int ip;
    if (!PyArg_ParseTuple(args, "Oi", &frame_obj, &ip)) {
        return NULL;
    }
    InterpreterFrame *frame = get_interpreter_frame(frame_obj);
    if (!frame) {
        return NULL;
    }
    assert(frame->f_code);
    assert(frame->prev_instr);
    // See _PyInterpreterFrame_LASTI
    // https://github.com/python/cpython/blob/3.12/Include/internal/pycore_frame.h#L77
    frame->prev_instr = (_Py_CODEUNIT *)((intptr_t)_PyCode_CODE(frame->f_code) + (intptr_t)ip);
    Py_RETURN_NONE;
}

static PyObject *set_frame_sp(PyObject *self, PyObject *args) {
    PyObject *frame_obj;
    int sp;
    if (!PyArg_ParseTuple(args, "Oi", &frame_obj, &sp)) {
        return NULL;
    }
    InterpreterFrame *frame = get_interpreter_frame(frame_obj);
    if (!frame) {
        return NULL;
    }
    assert(frame->stacktop >= 0);

    int limit = frame->f_code->co_stacksize + frame->f_code->co_nlocalsplus;
    if (sp < 0 || sp >= limit) {
        PyErr_SetString(PyExc_IndexError, "Stack pointer out of bounds");
        return NULL;
    }

    if (sp > frame->stacktop) {
        for (int i = frame->stacktop; i < sp; i++) {
            frame->localsplus[i] = NULL;
        }
    }

    frame->stacktop = sp;
    Py_RETURN_NONE;
}

static PyObject *set_generator_frame_state(PyObject *self, PyObject *args) {
    PyObject *gen_arg;
    int ip;
    if (!PyArg_ParseTuple(args, "Oi", &gen_arg, &ip)) {
        return NULL;
    }
    if (!PyGen_Check(gen_arg)) {
        PyErr_SetString(PyExc_TypeError, "Input object is not a generator");
        return NULL;
    }
    PyGenObject *gen = (PyGenObject *)gen_arg;
    // Disallow changing the frame state if the generator is complete
    // or has been closed, with the assumption that various parts
    // have now been torn down. The generator should be recreated before
    // the frame state is changed.
    if (gen->gi_frame_state >= FRAME_COMPLETED) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot set frame state if generator is complete");
        return NULL;
    }
    // TODO: check the value is one of the known constants?
    gen->gi_frame_state = (int8_t)ip;
    Py_RETURN_NONE;
}

static PyObject *set_frame_stack_at(PyObject *self, PyObject *args) {
    PyObject *frame_obj;
    int index;
    PyObject *unset;
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "OiOO", &frame_obj, &index, &unset, &obj)) {
        return NULL;
    }
    if (!PyBool_Check(unset)) {
        PyErr_SetString(PyExc_TypeError, "Expected a boolean indicating whether to unset the stack object");
        return NULL;
    }
    InterpreterFrame *frame = get_interpreter_frame(frame_obj);
    if (!frame) {
        return NULL;
    }
    assert(frame->stacktop >= 0);

    int limit = frame->f_code->co_stacksize + frame->f_code->co_nlocalsplus;
    if (index < 0 || index >= limit) {
        PyErr_SetString(PyExc_IndexError, "Index out of bounds");
        return NULL;
    }

    PyObject *prev = frame->localsplus[index];
    if (Py_IsTrue(unset)) {
        frame->localsplus[index] = NULL;
    } else {
        Py_INCREF(obj);
        frame->localsplus[index] = obj;
    }

    if (index < frame->stacktop) {
        Py_XDECREF(prev);
    }

    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
        {"get_frame_ip",  get_frame_ip, METH_VARARGS, "Get instruction pointer from a frame or generator."},
        {"set_frame_ip",  set_frame_ip, METH_VARARGS, "Set instruction pointer in a frame or generator."},
        {"get_frame_sp",  get_frame_sp, METH_VARARGS, "Get stack pointer from a frame or generator."},
        {"set_frame_sp",  set_frame_sp, METH_VARARGS, "Set stack pointer in a frame or generator."},
        {"get_frame_stack_at",  get_frame_stack_at, METH_VARARGS, "Get an object from a frame or generator's stack, as an (is_null, obj) tuple."},
        {"set_frame_stack_at",  set_frame_stack_at, METH_VARARGS, "Set or unset an object on the stack of a frame or generator."},
        {"get_generator_frame_state",  get_generator_frame_state, METH_VARARGS, "Get frame state from a generator."},
        {"set_generator_frame_state",  set_generator_frame_state, METH_VARARGS, "Set frame state of a generator."},
        {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "frame", NULL, -1, methods};

PyMODINIT_FUNC PyInit_frame(void) {
    return PyModule_Create(&module);
}