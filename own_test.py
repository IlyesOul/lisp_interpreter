# from lab import tokenize
# from scheme_utils import SchemeSyntaxError, number_or_symbol


# def parse(tokens):
#     """
#     Parses a list of token strings and outputs a tree-like representation where:
#         * symbols are represented as Python strings
#         * numbers are represented as Python ints or floats
#         * S-sourceessions are represented as Python lists

#     Hint: Make use of number_or_symbol imported from scheme_utils

#     >>> parse(['+'])
#     '+'
#     >>> parse(['-867.5309'])
#     -867.5309
#     >>> parse(['(', '(', 'parse', 'these', 'tokens', ')', 'here', ')'])
#     [['parse', 'these', 'tokens'], 'here']
#     """

#     result = parse_helper(tokens, 0)  # recursive result

#     if result[1] < len(tokens):  # extra items
#         raise SchemeSyntaxError("Extra items in expression")

#     return result[0]  # kick off recursion


# def parse_helper(tokens, index):
#     """
#     Helper function that recursively parses a list of tokens, starting from index
#     """

#     # Check bounds
#     if index >= len(tokens):
#         return [], index

#     if tokens[index] not in "()":  # either keyword or number
#         return number_or_symbol(tokens[index]), index + 1
#     elif tokens[index] == "(":  # start of sublist
#         curr_index = index + 1
#         inner_expr = []

#         # Check the next token
#         while curr_index < len(tokens) and tokens[curr_index] != ")":
#             recursive_val, ending_index = parse_helper(tokens, curr_index)
#             inner_expr.append(recursive_val)  # unconditionally append

#             # Update pointer
#             curr_index = ending_index

#         if curr_index < len(tokens) and tokens[curr_index] != ")":
#             raise SchemeSyntaxError("expression wasn't closed")

#         return inner_expr, curr_index + 1
#     else:  # end of sublist -> return []
#         return [], index + 1


# print(parse(tokenize("(nested (expressions (test) (is here) ((((now))))))")))
