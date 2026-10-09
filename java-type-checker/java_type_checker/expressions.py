# -*- coding: utf-8 -*-

from .types import JavaBuiltInTypes, JavaTypeError, NoSuchJavaMethod


class JavaExpression(object):
    """AST for simple Java expressions.

    Note that this library deals only with compile-time types, and this class therefore does not
    actually *evaluate* expressions.
    """

    def static_type(self):
        """Returns the compile-time type of this expression as a JavaType.

        Subclasses must override this method.
        """
        raise NotImplementedError(type(self).__name__ + " must override static_type()")

    def check_types(self):
        """Examines the structure of this expression for static type errors.

        Raises a JavaTypeError if there is an error. If there is no error, this method has no effect
        and returns nothing.

        Subclasses must override this method.
        """
        raise NotImplementedError(type(self).__name__ + " must override check_types()")


class JavaVariable(JavaExpression):
    """An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.

    In a real Java language implementation, the declared_type would be filled in by a name resolver
    after the initial construction of the AST. In this sample project, however, we simply specify
    the declared_type for every variable reference.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable (str)
        self.declared_type = declared_type  #: The declared type of the variable (JavaType)
    def static_type(self):
        return self.declared_type
    def check_types(self):
        return


class JavaLiteral(JavaExpression):
    """A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (JavaType)
    def static_type(self):
        return self.type
    def check_types(self):
        return


class JavaNullLiteral(JavaLiteral):
    """The literal value `null` in Java code.
    """
    def __init__(self):
        super().__init__("null", JavaBuiltInTypes.NULL)


class JavaAssignment(JavaExpression):
    """The assignment of a new value to a variable.

    Attributes:
        lhs (JavaVariable): The variable whose value this assignment updates.
        rhs (JavaExpression): The expression whose value will be assigned to the lhs.
    """
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def static_type(self):
        print (self.lhs.static_type)
        return self.lhs.static_type()
    def check_types(self):
        self.lhs.check_types()
        self.rhs.check_types()
        if (self.static_type() == self.rhs.static_type()):
            return
        if (self.rhs.static_type().is_subtype_of(self.lhs.static_type())):
            return
        else:
            raise JavaTypeMismatchError(
                "Cannot assign {0} to variable {1} of type {2}".format(
                    self.rhs.static_type().name,
                    self.lhs.name,
                    self.lhs.static_type().name))



class JavaMethodCall(JavaExpression):
    """A Java method invocation.

    For example, in this Java code::

        foo.bar(0, 1)

    - The receiver is `JavaVariable(foo, JavaObjectType(...))`
    - The method_name is `"bar"`
    - The args are `[JavaLiteral("0", JavaBuiltInTypes.INT), ...etc...]`

    Attributes:
        receiver (JavaExpression): The object whose method we are calling
        method_name (String): The name of the method to call
        args (list of Expressions): The arguments to pass to the method
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver
        self.method_name = method_name
        self.args = args
    def static_type(self):
        return self.receiver.static_type().method_named(self.method_name).return_type
    def check_types(self):
        self.receiver.check_types()
        for arg in self.args:
            arg.check_types()
        if (self.receiver.static_type() == JavaBuiltInTypes.NULL):
            raise NoSuchJavaMethod(
                "Cannot invoke method {0}() on null".format(
                    self.method_name
                )
            )
        if (self.receiver.static_type().is_subtype_of(JavaBuiltInTypes.INT) or self.receiver.static_type().is_subtype_of(JavaBuiltInTypes.DOUBLE) or self.receiver.static_type().is_subtype_of(JavaBuiltInTypes.BOOLEAN)):
            raise NoSuchJavaMethod(
                "Type {0} does not have methods".format(
                    self.receiver.static_type().name
                )
            )
        if not (self.receiver.static_type().method_named(self.method_name)):
            raise NoSuchJavaMethod(
                "{0} has no method named {1}".format(
                    self.receiver.static_type().name,
                    self.method_name
                )
            )
        if not (len(self.args) == len(self.receiver.static_type().method_named(self.method_name).parameter_types)):
            raise JavaArgumentCountError(
                "Wrong number of arguments for {0}: expected {1}, got {2}".format(
                    self.receiver.static_type().name +"."+ self.method_name +"()" ,
                    len(self.receiver.static_type().method_named(self.method_name).parameter_types),
                    len(self.args))
            )
        for (parameter, argument) in zip(self.receiver.static_type().method_named(self.method_name).parameter_types, self.args):
            if not (argument.static_type().is_subtype_of(parameter)):
                raise JavaTypeMismatchError(
                    "{0} expects arguments of type {1}, but got {2}".format(
                        self.receiver.static_type().name +"."+ self.method_name +"()",
                        _names(self.receiver.static_type().method_named(self.method_name).parameter_types),
                        _names([arguments.static_type() for arguments in self.args])
                    )
                )


class JavaConstructorCall(JavaExpression):
    """
    A Java object instantiation

    For example, in this Java code::

        new Foo(0, 1, 2)

    - The instantiated_type is `JavaObjectType("Foo", ...)`
    - The args are `[JavaLiteral("0", JavaBuiltInTypes.INT), ...etc...]`

    Attributes:
        instantiated_type (JavaType): The type to instantiate
        args (list of Expressions): Constructor arguments
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type
        self.args = args


class JavaTypeMismatchError(JavaTypeError):
    """Indicates that one or more expressions do not evaluate to the correct type.
    """
    pass


class JavaArgumentCountError(JavaTypeError):
    """Indicates that a call to a method or constructor has the wrong number of arguments.
    """
    pass


class JavaIllegalInstantiationError(JavaTypeError):
    """Raised in response to `new Foo()` where `Foo` is not an instantiable type.
    """
    pass


def _names(named_things):
    """Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
