"""
6.101 Lab:
LISP Interpreter Part 2
"""

#!/usr/bin/env python3

# import typing  # optional import
# import pprint  # optional import
# import enum    # optional import

# import doctest
import os
import sys

from scheme_utils import (
    number_or_symbol,
    SchemeEvaluationError,
    SchemeNameError,
    SchemeSyntaxError,
    SchemeREPL,
)

sys.setrecursionlimit(20_000)


####################################################################
# region                  Pairs
####################################################################
class Pair:
    """
    Class representing a con object
    """

    def __init__(self, car, cdr):
        """
        Initializer for pair object. Accepts car and cdr as arguments
        """
        self.car = car
        self.cdr = cdr

    def __str__(self):
        """
        String representation of pair object
        """
        return f"cons({str(self.car)}, {str(self.cdr)})"

    def __repr__(self):
        """
        String representation of pair object
        """
        return f"cons({str(self.car)}, {str(self.cdr)})"


# endregion
####################################################################
# region                  Frames
####################################################################
class Frame:
    """
    Class that represents a frame object in the interpreter;

    Contains attributes "variables", used for variable definition and
    lookup in the frame, and "enclosing", which is a pointer to
    this frame's enclosing one
    """

    def __init__(self, parent_frame=None):
        """
        Initializer that accepts enclosing frame as argument (none for initial frame)
        """
        self.variables = {}
        self.enclosing = parent_frame

    def set_definitions(self, variable_def: dict):
        """
        Function that accepts a variable-definition dictionary and sets
        the combination in the frame's variable dictionary
        """
        self.variables.update(variable_def)

    def lookup(self, variable_name):
        """
        Function that looks up variable value in this frame's
        variable dictionary; traverses enclosing frames hierarchy
        if not found, and raises SchemeNameError exception if not found
        """
        variable_value = self.variables.get(variable_name, None)
        if variable_value is not None:
            return (variable_value, self)  # value found
        else:  # traverse hierarchy
            if self.enclosing:
                return self.enclosing.lookup(variable_name)
            else:  # initial frame
                if not variable_value:  # not found
                    raise SchemeNameError(f"{variable_name} not defined in any frames")

        return None

    def delete_definition(self, variable_name):
        """
        Function that deletes variable in frame in which it is found
        """
        _, frame = self.lookup(variable_name)
        del frame.variables[variable_name]  # delete value at frame

    def __str__(self):
        """
        String representation of frame
        """
        return f"Frame w/enclosing {self.enclosing} and variables: {self.variables}"


def make_initial_frame():
    """
    Function that takes no arguments and returns a single new frame
    representing the initial frame
    """
    initial_frame = Frame()
    initial_frame.set_definitions(SCHEME_BUILTINS)  # builtins
    return Frame(initial_frame)  # has initial as pointer


# endregion
####################################################################
# region                  Functions
####################################################################
class Function:
    """
    Class that represents a function object in the interpreter;

    Contains attributes 'parameters', 'body', and a pointer to the
    frame the function is defined in
    """

    def __init__(self, params, body, enclosing_frame=None):
        """
        Initializer that accepts enclosing frame, parameters, and
        function body as parameters
        """
        self.params = params
        self.body = body
        self.enclosing = enclosing_frame

    def __call__(self, *args):
        """
        Executes the function by binding arguments to parameters in a new
        local frame and evaluating the body.
        """
        if len(args) != len(self.params):
            raise SchemeEvaluationError(
                f"Expected {len(self.params)} arguments, but got {len(args)}"
            )

        # Create a new local frame whose parent is the function's enclosing frame
        new_frame = Frame(self.enclosing)

        # Bind the parameters to the passed arguments
        new_frame.set_definitions(
            {name: value for name, value in zip(self.params, args)}
        )

        # Evaluate the body in the context of this new frame
        return evaluate(self.body, new_frame)

    def __str__(self):
        """
        String representation of frame
        """
        return f"Function w/params {self.params}, body {self.body}, and enclosing \
            frame {self.enclosing}"


# endregion
####################################################################
# region                  Tokenization
####################################################################


def tokenize(source: str):
    r"""
    Takes source, a string, and returns a list of individual token strings.
    Ignores comments and whitespace.

    >>> tokenize(' + ')
    ['+']
    >>> tokenize('-867.5309')
    ['-867.5309']
    >>> s = "((parse   these \n tokens) ;but ignore comments\n here );)"
    >>> tokenize(s)
    ['(', '(', 'parse', 'these', 'tokens', ')', 'here', ')']
    """

    tokens, i = [], 0
    new_source = source.replace("\n", "~")  # can't look at backslashes so rid them

    while i < len(new_source):
        if new_source[i] not in "() ":
            if new_source[i] == ";":  # comment case
                j = i + 1
                while j < len(new_source) and new_source[j] != "~":  # find backslash
                    j += 1
                i = j  # skipping comments
            elif new_source[i] == "~":  # skip newline
                i += 1
            else:  # non-comment
                j = i + 1
                word = new_source[i]
                while j < len(new_source) and new_source[j] not in "();~ ":  # scan
                    word += new_source[j]
                    j += 1
                tokens.append(word)
                i = j  # start off where j ended
        else:
            if new_source[i] != " ":
                tokens.append(new_source[i])
            i += 1

    return tokens


# endregion
####################################################################
# region                  Parsing
####################################################################


def parse(tokens):
    """
    Parses a list of token strings and outputs a tree-like representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-sourceessions are represented as Python lists

    Hint: Make use of number_or_symbol imported from scheme_utils

    >>> parse(['+'])
    '+'
    >>> parse(['-867.5309'])
    -867.5309
    >>> parse(['(', '(', 'parse', 'these', 'tokens', ')', 'here', ')'])
    [['parse', 'these', 'tokens'], 'here']
    """
    if not tokens:
        raise SchemeSyntaxError("no tokens provided")

    result = parse_helper(tokens, 0)  # recursive result

    if result[1] != len(tokens):  # extra items
        raise SchemeSyntaxError("Extra items in expression")

    return result[0]  # kick off recursion


def parse_helper(tokens, index):
    """
    Helper function that recursively parses a list of tokens, starting from index
    """

    # Check bounds
    if index >= len(tokens):
        raise SchemeSyntaxError("Incomplete expression")

    if tokens[index] not in "()":  # either keyword or number
        return number_or_symbol(tokens[index]), index + 1
    elif tokens[index] == "(":  # start of sublist
        curr_index = index + 1
        inner_expr = []

        # Check the next token
        while curr_index < len(tokens) and tokens[curr_index] != ")":
            recursive_val, ending_index = parse_helper(tokens, curr_index)
            inner_expr.append(recursive_val)  # unconditionally append

            # Update pointer
            curr_index = ending_index

        if curr_index >= len(tokens) or tokens[curr_index] != ")":
            raise SchemeSyntaxError("expression wasn't closed")

        return inner_expr, curr_index + 1
    else:  # started with ')' -> raise exception
        raise SchemeSyntaxError("started incorrectly")


# endregion
####################################################################
# region                       Evaluation
####################################################################


def evaluate(tree, frame: Frame = None):
    """
    Given tree, a fully parsed sourceession, and an optional frame
    evaluates and outputs the result of
    evaluating sourceession according to the rules of the Scheme language.

    >>> evaluate(6.101)
    6.101
    >>> evaluate(['+', 3, ['-', 3, 1, 1], 2])
    6
    """
    if not frame:  # create current frame if none is provided
        frame = make_initial_frame()

    if not tree:  # empty expression
        # raise SchemeEvaluationError("Empty line")
        return []

    # Easier for checking callability
    custom_functions = (
        "lambda",
        "define",
        "if",
        "and",
        "or",
        "begin",
        "del",
        "let",
        "set!",
    )

    def evaluate_helper(tree, current_frame: Frame):
        """
        Helper function that recursively evaluates expression
        """

        if isinstance(tree, str):  # built-in symbol
            if tree in custom_functions:
                return tree
            return current_frame.lookup(tree)[0]  # handles BUILTIN in initial frame
        elif isinstance(tree, (int, float, bool)):  # number or boolean
            return tree
        elif not tree:
            return []
        else:  # s-expression
            # if not tree:  # Check for empty list
            #     raise SchemeEvaluationError("Cannot evaluate empty list")

            s_expression = tree
            operator = evaluate_helper(
                s_expression[0], current_frame
            )  # obtain operator

            if (
                not callable(operator) and operator not in custom_functions
            ):  # ensure operator is a function
                raise SchemeEvaluationError("First item in expression is not callable")

            if operator == "define":  # defining variable/function
                # Set variable values and return
                variable_name = s_expression[1]

                if isinstance(variable_name, list):  # shorthand function
                    var_value = Function(
                        variable_name[1:], s_expression[2], current_frame
                    )
                    variable_name = variable_name[0]
                else:
                    var_value = evaluate_helper(s_expression[2], current_frame)

                current_frame.set_definitions({variable_name: var_value})
                return var_value
            elif operator == "lambda":  # defining function
                return Function(
                    s_expression[1], s_expression[2], current_frame
                )  # define/return function
            elif operator == "if":  # conditional
                evald_pred = evaluate_helper(s_expression[1], current_frame)

                if (
                    evald_pred is not False and evald_pred != "#f"
                ):  # true or false check
                    return evaluate_helper(s_expression[2], current_frame)
                else:
                    return evaluate_helper(s_expression[3], current_frame)
            elif operator == "and":
                for expr in s_expression[1:]:
                    if not evaluate_helper(expr, current_frame):  # break at first false
                        return False
                return True
            elif operator == "or":
                for expr in s_expression[1:]:
                    if evaluate_helper(expr, current_frame):  # break at first false
                        return True
                return False
            elif operator == "begin":
                if len(s_expression) < 2:
                    raise SchemeEvaluationError("not enough args for begin")
                for expr in s_expression[1:-1]:  # evaluate earlier expressions
                    evaluate(expr, current_frame)
                return evaluate(s_expression[-1], current_frame)  # value of interest
            elif operator == "del":
                if len(s_expression) > 1:
                    var_name = s_expression[1]
                    if not isinstance(var_name, str):
                        raise SchemeEvaluationError("var name not string for deletion")
                    val, frame = current_frame.lookup(var_name)
                    if frame != current_frame:
                        raise SchemeNameError(f"{var_name} not defined locally")
                    current_frame.delete_definition(var_name)
                    return val
            elif operator == "let":
                new_definitions = {}
                for pairing in s_expression[1]:
                    new_definitions[pairing[0]] = evaluate(
                        pairing[1], current_frame
                    )  # evaluate VALs
                local_frame = Frame(current_frame)
                local_frame.set_definitions(new_definitions)  # bind new values
                return evaluate(
                    s_expression[-1], local_frame
                )  # evaluate body in local frame
            elif operator == "set!":
                # Evaluate expression
                var, expr = s_expression[1], s_expression[2]
                expr_value = evaluate(expr, current_frame)

                # Bind value in appropriate frame
                defining_frame = current_frame.lookup(var)[1]
                defining_frame.set_definitions({var: expr_value})
                return expr_value
            else:  # calling function OR working with regular s_expression
                # Arguments or inside of s_expression
                arg_evaled = [
                    evaluate_helper(arg, current_frame) for arg in s_expression[1:]
                ]

                if callable(operator):  # built-in
                    try:
                        return operator(*arg_evaled)  # compute
                    except TypeError:
                        raise SchemeEvaluationError(
                            f"Too few/many arguments passed to {operator}"
                        )
                else:  # calling function OR working with regular s_expression
                    # Arguments or inside of s_expression
                    arg_evaled = [
                        evaluate_helper(arg, current_frame) for arg in s_expression[1:]
                    ]

                    # If it's a custom function, just call it directly
                    if isinstance(operator, Function):
                        return operator(*arg_evaled)

                    # Otherwise it's a built-in Python function
                    else:
                        try:
                            return operator(*arg_evaled)  # compute
                        except TypeError:
                            raise SchemeEvaluationError(
                                f"Too few/many arguments passed to {operator}"
                            )

    return evaluate_helper(tree, frame)


# endregion
####################################################################
# region                      Built-ins
####################################################################


def builtin_mul(*args):
    """
    Computes the product of two or more evaluated numeric args.
    >>> builtin_mul(1, 2)
    2
    >>> builtin_mul(1, 2, -3)
    -6
    """
    if len(args) == 2:
        return args[0] * args[1]

    first_num, *rest_nums = args
    return first_num * builtin_mul(*rest_nums)


def builtin_sub(*args):
    """
    Computes subtraction of two or more evaluated numeric args.
    >>> builtin_sub(1, 2)
    -1
    >>> builtin_sub(1, 2, -3)
    2
    """

    if len(args) == 1:  # return negated first
        return -args[0]

    first_num, *rest_nums = args
    return first_num - sum(rest_nums)  # subtract sum of rest


def builtin_div(*args):
    """
    Computes division of two or more evaluated numeric args.
    >>> builtin_sub(1, 2)
    .5
    >>> builtin_sub(5, 4)
    1.25
    """
    val = args[0]  # leftmost val
    if len(args) > 1:
        for i in range(1, len(args)):  # divide
            val /= args[i]
    return val


# ILYES MAKE THIS LESS REPETETIVE
def builtin_equals(*args):
    return all(args[i] == args[i + 1] for i in range(len(args) - 1))


def builtin_l(*args):
    return all(args[i] < args[i + 1] for i in range(len(args) - 1))


def builtin_le(*args):
    return all(args[i] <= args[i + 1] for i in range(len(args) - 1))


def builtin_g(*args):
    return all(args[i] > args[i + 1] for i in range(len(args) - 1))


def builtin_ge(*args):
    return all(args[i] >= args[i + 1] for i in range(len(args) - 1))


def cons(*args):
    """
    Creates and returns cons Pair object
    """
    if len(args) != 2:
        raise SchemeEvaluationError("incorrect # arguments passed to con object")
    return Pair(args[0], args[1])


def get_car(*args):
    """
    Retreives car for a cons object
    """
    if len(args) != 1 or not isinstance(args[0], Pair):
        raise SchemeEvaluationError("Incorrect # args for car or not using con")
    return args[0].car  # retreive


def get_cdr(*args):
    """
    Retreives cdr for a cons object
    """
    if len(args) != 1 or not isinstance(args[0], Pair):
        raise SchemeEvaluationError("Incorrect # args for cdr or not using con")
    return args[0].cdr  # retreive


def builtin_list(*args):
    """
        Constructs list in terms of pairs with args as items
    """
    def helper(i):
        if i == len(args) - 1:
            return Pair(args[i], [])  # base case
        pair = Pair(args[i], helper(i + 1))
        return pair

    if len(args) > 0:  # multiple items
        overall_con = Pair(args[0], [])
        if len(args) > 1:
            overall_con.cdr = helper(1)
        return overall_con
    else:
        return []


def length(ll: Pair):
    """
    Function returns length of passed linked list
    """

    # Base cases
    if not SCHEME_BUILTINS["list?"](ll):
        raise SchemeEvaluationError("wasn't passed LL for length")
    if ll == []:
        return 0

    curr_con = ll
    size = 0

    while isinstance(curr_con, Pair):  # while there's a con to iterate to
        size += 1
        curr_con = curr_con.cdr

    return size


def list_check(*args):
    """
    Function that tests if object is a linked list
    """
    if len(args) != 1:
        raise SchemeEvaluationError("more than one arg passed to list?")

    # make sure only other pairs until end
    curr_con = args[0]
    while isinstance(curr_con, Pair):
        curr_con = curr_con.cdr

    return curr_con == []


def value_at(*args):
    """
    Obtains value at an index in a list
    """
    if len(args) != 2:
        raise SchemeEvaluationError("list-ref takes 2 arguments")

    ls, index = args

    if ls == []:
        raise SchemeEvaluationError("empty list")

    curr = ls
    for _ in range(index):
        if not isinstance(curr, Pair):
            raise SchemeEvaluationError("index out of bounds or not a proper list")
        curr = curr.cdr

    if not isinstance(curr, Pair):
        raise SchemeEvaluationError("index out of bounds")

    return curr.car


def app(*args):
    """
    Function that creates a list which is a combination of passed ones
    """
    if len(args) == 0:
        return []

    if not all(list_check(arg) for arg in args):
        raise SchemeEvaluationError("wasn't passed list for append")

    res = args[-1]  # don't copy last list

    for i in range(len(args) - 2, -1, -1):
        curr_list = args[i]
        elements = []
        curr_val = curr_list

        # Traverse list and collect elements
        while isinstance(curr_val, Pair):
            elements.append(curr_val.car)
            curr_val = curr_val.cdr

        if curr_val != []:  # must be empty
            raise SchemeEvaluationError("wasn't given proper bounds")

        # Started from back so reverse
        for revsd in reversed(elements):
            res = Pair(revsd, res)

    return res


def evaluate_file(filename, frame=None):
    """
    Function that evaluates contents of file within optional frame
    """

    # Make a frame if none exists
    if not frame:
        frame = make_initial_frame()

    # Line-by-line evaluation
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = tokenize(text)
    index = 0
    last_result = None

    # Keep parsing until we run out of tokens
    while index < len(tokens):
        expr, index = parse_helper(tokens, index)  # parse
        last_result = evaluate(expr, frame)  # cascading evaluation

    return last_result


def not_func(*args):
    """
    Function that returns "not" value of passed expression
    """
    if len(args) != 1:
        raise SchemeEvaluationError("!=2 arguments passed to not")
    return args[0] is False


SCHEME_BUILTINS = {
    "+": lambda *args: sum(args),
    "*": builtin_mul,
    "-": builtin_sub,
    "/": builtin_div,
    "equal?": builtin_equals,
    "<": builtin_l,
    "<=": builtin_le,
    ">": builtin_g,
    ">=": builtin_ge,
    "cons": cons,
    "car": get_car,
    "cdr": get_cdr,
    "list": builtin_list,
    "list?": list_check,
    "length": length,
    "list-ref": value_at,
    "append": app,
    "not": not_func,
    "#t": True,
    "#f": False
}

# endregion
####################################################################
# region                       REPL
####################################################################

if __name__ == "__main__":
    run_doctest = False
    run_repl = True

    # if run_doctest:
    #     _doctest_flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    #     doctest.run_docstring_examples(evaluate, globals(), \
    # optionflags=_doctest_flags)
    #     #doctest.testmod(optionflags=_doctest_flags)  # runs ALL doctests

    if run_repl:
        init_frame = make_initial_frame()
        files = sys.argv[1:]

        for file in files:
            evaluate_file(file, init_frame)
        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
        SchemeREPL(sys.modules[__name__], verbose=True, repl_frame=init_frame).cmdloop()

    # print(builtin_list(1, 2, 3, 4, 5))

    r = sum([((lambda x: x*x) (x)) for x in [[ele for ele in [1, 2, 3] if ele > 2]]])

# endregion
