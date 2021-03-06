# -*- coding: utf-8 -*-
"""
    pygments.lexers.math
    ~~~~~~~~~~~~~~~~~~~~

    Lexers for math languages.

    :copyright: Copyright 2006-2012 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.lexer import Lexer, RegexLexer, bygroups, include, \
    combined, do_insertions
from pygments.token import Comment, String, Punctuation, Keyword, Name, \
    Operator, Number, Text, Generic

from pygments.lexers.agile import PythonLexer
from pygments.lexers import _scilab_builtins

__all__ = ['JuliaLexer', 'JuliaConsoleLexer', 'MuPADLexer', 'MatlabLexer',
           'MatlabSessionLexer', 'OctaveLexer', 'ScilabLexer', 'NumPyLexer',
           'RConsoleLexer', 'SLexer']


class JuliaLexer(RegexLexer):
    name = 'Julia'
    aliases = ['julia','jl']
    filenames = ['*.jl']
    mimetypes = ['text/x-julia','application/x-julia']

    builtins = [
        'exit','whos','edit','load','is','isa','isequal','typeof','tuple',
        'ntuple','uid','hash','finalizer','convert','promote','subtype',
        'typemin','typemax','realmin','realmax','sizeof','eps','promote_type',
        'method_exists','applicable','invoke','dlopen','dlsym','system',
        'error','throw','assert','new','Inf','Nan','pi','im',
    ]

    tokens = {
        'root': [
            (r'\n', Text),
            (r'[^\S\n]+', Text),
            (r'#.*$', Comment),
            (r'[]{}:(),;[@]', Punctuation),
            (r'\\\n', Text),
            (r'\\', Text),

            # keywords
            (r'(begin|while|for|in|return|break|continue|'
             r'macro|quote|let|if|elseif|else|try|catch|end|'
             r'bitstype|ccall|do)\b', Keyword),
            (r'(local|global|const)\b', Keyword.Declaration),
            (r'(module|import|export)\b', Keyword.Reserved),
            (r'(Bool|Int|Int8|Int16|Int32|Int64|Uint|Uint8|Uint16|Uint32|Uint64'
             r'|Float32|Float64|Complex64|Complex128|Any|Nothing|None)\b',
                Keyword.Type),

            # functions
            (r'(function)((?:\s|\\\s)+)',
                bygroups(Keyword,Name.Function), 'funcname'),

            # types
            (r'(type|typealias|abstract)((?:\s|\\\s)+)',
                bygroups(Keyword,Name.Class), 'typename'),

            # operators
            (r'==|!=|<=|>=|->|&&|\|\||::|<:|[-~+/*%=<>&^|.?!$]', Operator),
            (r'\.\*|\.\^|\.\\|\.\/|\\', Operator),

            # builtins
            ('(' + '|'.join(builtins) + r')\b',  Name.Builtin),

            # backticks
            (r'`(?s).*?`', String.Backtick),

            # chars
            (r"'(\\.|\\[0-7]{1,3}|\\x[a-fA-F0-9]{1,3}|\\u[a-fA-F0-9]{1,4}|\\U[a-fA-F0-9]{1,6}|[^\\\'\n])'", String.Char),

            # try to match trailing transpose
            (r'(?<=[.\w\)\]])\'', Operator),

            # strings
            (r'(?:[IL])"', String, 'string'),
            (r'[E]?"', String, combined('stringescape', 'string')),

            # names
            (r'@[a-zA-Z0-9_.]+', Name.Decorator),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', Name),

            # numbers
            (r'(\d+\.\d*|\d*\.\d+)([eE][+-]?[0-9]+)?', Number.Float),
            (r'\d+[eE][+-]?[0-9]+', Number.Float),
            (r'0[0-7]+', Number.Oct),
            (r'0[xX][a-fA-F0-9]+', Number.Hex),
            (r'\d+', Number.Integer)
        ],

        'funcname': [
            ('[a-zA-Z_][a-zA-Z0-9_]*', Name.Function, '#pop'),
            ('\([^\s\w{]{1,2}\)', Operator, '#pop'),
            ('[^\s\w{]{1,2}', Operator, '#pop'),
        ],

        'typename': [
            ('[a-zA-Z_][a-zA-Z0-9_]*', Name.Class, '#pop')
        ],

        'stringescape': [
            (r'\\([\\abfnrtv"\']|\n|N{.*?}|u[a-fA-F0-9]{4}|'
             r'U[a-fA-F0-9]{8}|x[a-fA-F0-9]{2}|[0-7]{1,3})', String.Escape)
        ],

        'string': [
            (r'"', String, '#pop'),
            (r'\\\\|\\"|\\\n', String.Escape), # included here for raw strings
            (r'\$(\([a-zA-Z0-9_]+\))?[-#0 +]*([0-9]+|[*])?(\.([0-9]+|[*]))?',
                String.Interpol),
            (r'[^\\"$]+', String),
            # quotes, dollar signs, and backslashes must be parsed one at a time
            (r'["\\]', String),
            # unhandled string formatting sign
            (r'\$', String)
        ],
    }

    def analyse_text(text):
        return shebang_matches(text, r'julia')


line_re  = re.compile('.*?\n')

class JuliaConsoleLexer(Lexer):
    """
    For Julia console sessions. Modeled after MatlabSessionLexer.
    """
    name = 'Julia console'
    aliases = ['jlcon']

    def get_tokens_unprocessed(self, text):
        jllexer = JuliaLexer(**self.options)

        curcode = ''
        insertions = []

        for match in line_re.finditer(text):
            line = match.group()

            if line.startswith('julia>'):
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, line[:3])]))
                curcode += line[3:]

            elif line.startswith('      '):

                idx = len(curcode)

                # without is showing error on same line as before...?
                line = "\n" + line
                token = (0, Generic.Traceback, line)
                insertions.append((idx, [token]))

            else:
                if curcode:
                    for item in do_insertions(
                        insertions, jllexer.get_tokens_unprocessed(curcode)):
                        yield item
                    curcode = ''
                    insertions = []

                yield match.start(), Generic.Output, line

        if curcode: # or item:
            for item in do_insertions(
                insertions, jllexer.get_tokens_unprocessed(curcode)):
                yield item


class MuPADLexer(RegexLexer):
    """
    A `MuPAD <http://www.mupad.com>`_ lexer.
    Contributed by Christopher Creutzig <christopher@creutzig.de>.

    *New in Pygments 0.8.*
    """
    name = 'MuPAD'
    aliases = ['mupad']
    filenames = ['*.mu']

    tokens = {
      'root' : [
        (r'//.*?$', Comment.Single),
        (r'/\*', Comment.Multiline, 'comment'),
        (r'"(?:[^"\\]|\\.)*"', String),
        (r'\(|\)|\[|\]|\{|\}', Punctuation),
        (r'''(?x)\b(?:
            next|break|end|
            axiom|end_axiom|category|end_category|domain|end_domain|inherits|
            if|%if|then|elif|else|end_if|
            case|of|do|otherwise|end_case|
            while|end_while|
            repeat|until|end_repeat|
            for|from|to|downto|step|end_for|
            proc|local|option|save|begin|end_proc|
            delete|frame
          )\b''', Keyword),
        (r'''(?x)\b(?:
            DOM_ARRAY|DOM_BOOL|DOM_COMPLEX|DOM_DOMAIN|DOM_EXEC|DOM_EXPR|
            DOM_FAIL|DOM_FLOAT|DOM_FRAME|DOM_FUNC_ENV|DOM_HFARRAY|DOM_IDENT|
            DOM_INT|DOM_INTERVAL|DOM_LIST|DOM_NIL|DOM_NULL|DOM_POLY|DOM_PROC|
            DOM_PROC_ENV|DOM_RAT|DOM_SET|DOM_STRING|DOM_TABLE|DOM_VAR
          )\b''', Name.Class),
        (r'''(?x)\b(?:
            PI|EULER|E|CATALAN|
            NIL|FAIL|undefined|infinity|
            TRUE|FALSE|UNKNOWN
          )\b''',
          Name.Constant),
        (r'\b(?:dom|procname)\b', Name.Builtin.Pseudo),
        (r'\.|,|:|;|=|\+|-|\*|/|\^|@|>|<|\$|\||!|\'|%|~=', Operator),
        (r'''(?x)\b(?:
            and|or|not|xor|
            assuming|
            div|mod|
            union|minus|intersect|in|subset
          )\b''',
          Operator.Word),
        (r'\b(?:I|RDN_INF|RD_NINF|RD_NAN)\b', Number),
        #(r'\b(?:adt|linalg|newDomain|hold)\b', Name.Builtin),
        (r'''(?x)
          ((?:[a-zA-Z_#][a-zA-Z_#0-9]*|`[^`]*`)
          (?:::[a-zA-Z_#][a-zA-Z_#0-9]*|`[^`]*`)*)(\s*)([(])''',
          bygroups(Name.Function, Text, Punctuation)),
        (r'''(?x)
          (?:[a-zA-Z_#][a-zA-Z_#0-9]*|`[^`]*`)
          (?:::[a-zA-Z_#][a-zA-Z_#0-9]*|`[^`]*`)*''', Name.Variable),
        (r'[0-9]+(?:\.[0-9]*)?(?:e[0-9]+)?', Number),
        (r'\.[0-9]+(?:e[0-9]+)?', Number),
        (r'.', Text)
      ],
      'comment' : [
        (r'[^*/]', Comment.Multiline),
        (r'/\*', Comment.Multiline, '#push'),
        (r'\*/', Comment.Multiline, '#pop'),
        (r'[*/]', Comment.Multiline)
      ]
    }


class MatlabLexer(RegexLexer):
    """
    For Matlab source code.
    Contributed by Ken Schutte <kschutte@csail.mit.edu>.

    *New in Pygments 0.10.*
    """
    name = 'Matlab'
    aliases = ['matlab']
    filenames = ['*.m']
    mimetypes = ['text/matlab']

    #
    # These lists are generated automatically.
    # Run the following in bash shell:
    #
    # for f in elfun specfun elmat; do
    #   echo -n "$f = "
    #   matlab -nojvm -r "help $f;exit;" | perl -ne \
    #   'push(@c,$1) if /^    (\w+)\s+-/; END {print q{["}.join(q{","},@c).qq{"]\n};}'
    # done
    #
    # elfun: Elementary math functions
    # specfun: Special Math functions
    # elmat: Elementary matrices and matrix manipulation
    #
    # taken from Matlab version 7.4.0.336 (R2007a)
    #
    elfun = ["sin","sind","sinh","asin","asind","asinh","cos","cosd","cosh",
             "acos","acosd","acosh","tan","tand","tanh","atan","atand","atan2",
             "atanh","sec","secd","sech","asec","asecd","asech","csc","cscd",
             "csch","acsc","acscd","acsch","cot","cotd","coth","acot","acotd",
             "acoth","hypot","exp","expm1","log","log1p","log10","log2","pow2",
             "realpow","reallog","realsqrt","sqrt","nthroot","nextpow2","abs",
             "angle","complex","conj","imag","real","unwrap","isreal","cplxpair",
             "fix","floor","ceil","round","mod","rem","sign"]
    specfun = ["airy","besselj","bessely","besselh","besseli","besselk","beta",
               "betainc","betaln","ellipj","ellipke","erf","erfc","erfcx",
               "erfinv","expint","gamma","gammainc","gammaln","psi","legendre",
               "cross","dot","factor","isprime","primes","gcd","lcm","rat",
               "rats","perms","nchoosek","factorial","cart2sph","cart2pol",
               "pol2cart","sph2cart","hsv2rgb","rgb2hsv"]
    elmat = ["zeros","ones","eye","repmat","rand","randn","linspace","logspace",
             "freqspace","meshgrid","accumarray","size","length","ndims","numel",
             "disp","isempty","isequal","isequalwithequalnans","cat","reshape",
             "diag","blkdiag","tril","triu","fliplr","flipud","flipdim","rot90",
             "find","end","sub2ind","ind2sub","bsxfun","ndgrid","permute",
             "ipermute","shiftdim","circshift","squeeze","isscalar","isvector",
             "ans","eps","realmax","realmin","pi","i","inf","nan","isnan",
             "isinf","isfinite","j","why","compan","gallery","hadamard","hankel",
             "hilb","invhilb","magic","pascal","rosser","toeplitz","vander",
             "wilkinson"]

    tokens = {
        'root': [
            # line starting with '!' is sent as a system command.  not sure what
            # label to use...
            (r'^!.*', String.Other),
            (r'%.*$', Comment),
            (r'^\s*function', Keyword, 'deffunc'),

            # from 'iskeyword' on version 7.11 (R2010):
            (r'(break|case|catch|classdef|continue|else|elseif|end|enumerated|'
             r'events|for|function|global|if|methods|otherwise|parfor|'
             r'persistent|properties|return|spmd|switch|try|while)\b', Keyword),

            ("(" + "|".join(elfun+specfun+elmat) + r')\b',  Name.Builtin),

            # operators:
            (r'-|==|~=|<|>|<=|>=|&&|&|~|\|\|?', Operator),
            # operators requiring escape for re:
            (r'\.\*|\*|\+|\.\^|\.\\|\.\/|\/|\\', Operator),

            # punctuation:
            (r'\[|\]|\(|\)|\{|\}|:|@|\.|,', Punctuation),
            (r'=|:|;', Punctuation),

            # quote can be transpose, instead of string:
            # (not great, but handles common cases...)
            (r'(?<=[\w\)\]])\'', Operator),

            (r'(?<![\w\)\]])\'', String, 'string'),
            ('[a-zA-Z_][a-zA-Z0-9_]*', Name),
            (r'.', Text),
        ],
        'string': [
            (r'[^\']*\'', String, '#pop')
        ],
        'deffunc': [
            (r'(\s*)(?:(.+)(\s*)(=)(\s*))?(.+)(\()(.*)(\))(\s*)',
             bygroups(Text.Whitespace, Text, Text.Whitespace, Punctuation,
                      Text.Whitespace, Name.Function, Punctuation, Text,
                      Punctuation, Text.Whitespace), '#pop'),
        ],
    }

    def analyse_text(text):
        if re.match('^\s*%', text, re.M): # comment
            return 0.9
        elif re.match('^!\w+', text, re.M): # system cmd
            return 0.9
        return 0.1


line_re  = re.compile('.*?\n')

class MatlabSessionLexer(Lexer):
    """
    For Matlab sessions.  Modeled after PythonConsoleLexer.
    Contributed by Ken Schutte <kschutte@csail.mit.edu>.

    *New in Pygments 0.10.*
    """
    name = 'Matlab session'
    aliases = ['matlabsession']

    def get_tokens_unprocessed(self, text):
        mlexer = MatlabLexer(**self.options)

        curcode = ''
        insertions = []

        for match in line_re.finditer(text):
            line = match.group()

            if line.startswith('>>'):
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, line[:3])]))
                curcode += line[3:]

            elif line.startswith('???'):

                idx = len(curcode)

                # without is showing error on same line as before...?
                line = "\n" + line
                token = (0, Generic.Traceback, line)
                insertions.append((idx, [token]))

            else:
                if curcode:
                    for item in do_insertions(
                        insertions, mlexer.get_tokens_unprocessed(curcode)):
                        yield item
                    curcode = ''
                    insertions = []

                yield match.start(), Generic.Output, line

        if curcode: # or item:
            for item in do_insertions(
                insertions, mlexer.get_tokens_unprocessed(curcode)):
                yield item


class OctaveLexer(RegexLexer):
    """
    For GNU Octave source code.

    *New in Pygments 1.5.*
    """
    name = 'Octave'
    aliases = ['octave']
    filenames = ['*.m']
    mimetypes = ['text/octave']

    # These lists are generated automatically.
    # Run the following in bash shell:
    #
    # First dump all of the Octave manual into a plain text file:
    #
    #   $ info octave --subnodes -o octave-manual
    #
    # Now grep through it:

    # for i in \
    #     "Built-in Function" "Command" "Function File" \
    #     "Loadable Function" "Mapping Function";
    # do
    #     perl -e '@name = qw('"$i"');
    #              print lc($name[0]),"_kw = [\n"';
    #
    #     perl -n -e 'print "\"$1\",\n" if /-- '"$i"': .* (\w*) \(/;' \
    #         octave-manual | sort | uniq ;
    #     echo "]" ;
    #     echo;
    # done

    # taken from Octave Mercurial changeset 8cc154f45e37 (30-jan-2011)

    builtin_kw = [ "addlistener", "addpath", "addproperty", "all",
                   "and", "any", "argnames", "argv", "assignin",
                   "atexit", "autoload",
                   "available_graphics_toolkits", "beep_on_error",
                   "bitand", "bitmax", "bitor", "bitshift", "bitxor",
                   "cat", "cell", "cellstr", "char", "class", "clc",
                   "columns", "command_line_path",
                   "completion_append_char", "completion_matches",
                   "complex", "confirm_recursive_rmdir", "cputime",
                   "crash_dumps_octave_core", "ctranspose", "cumprod",
                   "cumsum", "debug_on_error", "debug_on_interrupt",
                   "debug_on_warning", "default_save_options",
                   "dellistener", "diag", "diff", "disp",
                   "doc_cache_file", "do_string_escapes", "double",
                   "drawnow", "e", "echo_executing_commands", "eps",
                   "eq", "errno", "errno_list", "error", "eval",
                   "evalin", "exec", "exist", "exit", "eye", "false",
                   "fclear", "fclose", "fcntl", "fdisp", "feof",
                   "ferror", "feval", "fflush", "fgetl", "fgets",
                   "fieldnames", "file_in_loadpath", "file_in_path",
                   "filemarker", "filesep", "find_dir_in_path",
                   "fixed_point_format", "fnmatch", "fopen", "fork",
                   "formula", "fprintf", "fputs", "fread", "freport",
                   "frewind", "fscanf", "fseek", "fskipl", "ftell",
                   "functions", "fwrite", "ge", "genpath", "get",
                   "getegid", "getenv", "geteuid", "getgid",
                   "getpgrp", "getpid", "getppid", "getuid", "glob",
                   "gt", "gui_mode", "history_control",
                   "history_file", "history_size",
                   "history_timestamp_format_string", "home",
                   "horzcat", "hypot", "ifelse",
                   "ignore_function_time_stamp", "inferiorto",
                   "info_file", "info_program", "inline", "input",
                   "intmax", "intmin", "ipermute",
                   "is_absolute_filename", "isargout", "isbool",
                   "iscell", "iscellstr", "ischar", "iscomplex",
                   "isempty", "isfield", "isfloat", "isglobal",
                   "ishandle", "isieee", "isindex", "isinteger",
                   "islogical", "ismatrix", "ismethod", "isnull",
                   "isnumeric", "isobject", "isreal",
                   "is_rooted_relative_filename", "issorted",
                   "isstruct", "isvarname", "kbhit", "keyboard",
                   "kill", "lasterr", "lasterror", "lastwarn",
                   "ldivide", "le", "length", "link", "linspace",
                   "logical", "lstat", "lt", "make_absolute_filename",
                   "makeinfo_program", "max_recursion_depth", "merge",
                   "methods", "mfilename", "minus", "mislocked",
                   "mkdir", "mkfifo", "mkstemp", "mldivide", "mlock",
                   "mouse_wheel_zoom", "mpower", "mrdivide", "mtimes",
                   "munlock", "nargin", "nargout",
                   "native_float_format", "ndims", "ne", "nfields",
                   "nnz", "norm", "not", "numel", "nzmax",
                   "octave_config_info", "octave_core_file_limit",
                   "octave_core_file_name",
                   "octave_core_file_options", "ones", "or",
                   "output_max_field_width", "output_precision",
                   "page_output_immediately", "page_screen_output",
                   "path", "pathsep", "pause", "pclose", "permute",
                   "pi", "pipe", "plus", "popen", "power",
                   "print_empty_dimensions", "printf",
                   "print_struct_array_contents", "prod",
                   "program_invocation_name", "program_name",
                   "putenv", "puts", "pwd", "quit", "rats", "rdivide",
                   "readdir", "readlink", "read_readline_init_file",
                   "realmax", "realmin", "rehash", "rename",
                   "repelems", "re_read_readline_init_file", "reset",
                   "reshape", "resize", "restoredefaultpath",
                   "rethrow", "rmdir", "rmfield", "rmpath", "rows",
                   "save_header_format_string", "save_precision",
                   "saving_history", "scanf", "set", "setenv",
                   "shell_cmd", "sighup_dumps_octave_core",
                   "sigterm_dumps_octave_core", "silent_functions",
                   "single", "size", "size_equal", "sizemax",
                   "sizeof", "sleep", "source", "sparse_auto_mutate",
                   "split_long_rows", "sprintf", "squeeze", "sscanf",
                   "stat", "stderr", "stdin", "stdout", "strcmp",
                   "strcmpi", "string_fill_char", "strncmp",
                   "strncmpi", "struct", "struct_levels_to_print",
                   "strvcat", "subsasgn", "subsref", "sum", "sumsq",
                   "superiorto", "suppress_verbose_help_message",
                   "symlink", "system", "tic", "tilde_expand",
                   "times", "tmpfile", "tmpnam", "toc", "toupper",
                   "transpose", "true", "typeinfo", "umask", "uminus",
                   "uname", "undo_string_escapes", "unlink", "uplus",
                   "upper", "usage", "usleep", "vec", "vectorize",
                   "vertcat", "waitpid", "warning", "warranty",
                   "whos_line_format", "yes_or_no", "zeros",
                   "inf", "Inf", "nan", "NaN"]

    command_kw = [ "close", "load", "who", "whos", ]

    function_kw = [ "accumarray", "accumdim", "acosd", "acotd",
                   "acscd", "addtodate", "allchild", "ancestor",
                   "anova", "arch_fit", "arch_rnd", "arch_test",
                   "area", "arma_rnd", "arrayfun", "ascii", "asctime",
                   "asecd", "asind", "assert", "atand",
                   "autoreg_matrix", "autumn", "axes", "axis", "bar",
                   "barh", "bartlett", "bartlett_test", "beep",
                   "betacdf", "betainv", "betapdf", "betarnd",
                   "bicgstab", "bicubic", "binary", "binocdf",
                   "binoinv", "binopdf", "binornd", "bitcmp",
                   "bitget", "bitset", "blackman", "blanks",
                   "blkdiag", "bone", "box", "brighten", "calendar",
                   "cast", "cauchy_cdf", "cauchy_inv", "cauchy_pdf",
                   "cauchy_rnd", "caxis", "celldisp", "center", "cgs",
                   "chisquare_test_homogeneity",
                   "chisquare_test_independence", "circshift", "cla",
                   "clabel", "clf", "clock", "cloglog", "closereq",
                   "colon", "colorbar", "colormap", "colperm",
                   "comet", "common_size", "commutation_matrix",
                   "compan", "compare_versions", "compass",
                   "computer", "cond", "condest", "contour",
                   "contourc", "contourf", "contrast", "conv",
                   "convhull", "cool", "copper", "copyfile", "cor",
                   "corrcoef", "cor_test", "cosd", "cotd", "cov",
                   "cplxpair", "cross", "cscd", "cstrcat", "csvread",
                   "csvwrite", "ctime", "cumtrapz", "curl", "cut",
                   "cylinder", "date", "datenum", "datestr",
                   "datetick", "datevec", "dblquad", "deal",
                   "deblank", "deconv", "delaunay", "delaunayn",
                   "delete", "demo", "detrend", "diffpara", "diffuse",
                   "dir", "discrete_cdf", "discrete_inv",
                   "discrete_pdf", "discrete_rnd", "display",
                   "divergence", "dlmwrite", "dos", "dsearch",
                   "dsearchn", "duplication_matrix", "durbinlevinson",
                   "ellipsoid", "empirical_cdf", "empirical_inv",
                   "empirical_pdf", "empirical_rnd", "eomday",
                   "errorbar", "etime", "etreeplot", "example",
                   "expcdf", "expinv", "expm", "exppdf", "exprnd",
                   "ezcontour", "ezcontourf", "ezmesh", "ezmeshc",
                   "ezplot", "ezpolar", "ezsurf", "ezsurfc", "factor",
                   "factorial", "fail", "fcdf", "feather", "fftconv",
                   "fftfilt", "fftshift", "figure", "fileattrib",
                   "fileparts", "fill", "findall", "findobj",
                   "findstr", "finv", "flag", "flipdim", "fliplr",
                   "flipud", "fpdf", "fplot", "fractdiff", "freqz",
                   "freqz_plot", "frnd", "fsolve",
                   "f_test_regression", "ftp", "fullfile", "fzero",
                   "gamcdf", "gaminv", "gampdf", "gamrnd", "gca",
                   "gcbf", "gcbo", "gcf", "genvarname", "geocdf",
                   "geoinv", "geopdf", "geornd", "getfield", "ginput",
                   "glpk", "gls", "gplot", "gradient",
                   "graphics_toolkit", "gray", "grid", "griddata",
                   "griddatan", "gtext", "gunzip", "gzip", "hadamard",
                   "hamming", "hankel", "hanning", "hggroup",
                   "hidden", "hilb", "hist", "histc", "hold", "hot",
                   "hotelling_test", "housh", "hsv", "hurst",
                   "hygecdf", "hygeinv", "hygepdf", "hygernd",
                   "idivide", "ifftshift", "image", "imagesc",
                   "imfinfo", "imread", "imshow", "imwrite", "index",
                   "info", "inpolygon", "inputname", "interpft",
                   "interpn", "intersect", "invhilb", "iqr", "isa",
                   "isdefinite", "isdir", "is_duplicate_entry",
                   "isequal", "isequalwithequalnans", "isfigure",
                   "ishermitian", "ishghandle", "is_leap_year",
                   "isletter", "ismac", "ismember", "ispc", "isprime",
                   "isprop", "isscalar", "issquare", "isstrprop",
                   "issymmetric", "isunix", "is_valid_file_id",
                   "isvector", "jet", "kendall",
                   "kolmogorov_smirnov_cdf",
                   "kolmogorov_smirnov_test", "kruskal_wallis_test",
                   "krylov", "kurtosis", "laplace_cdf", "laplace_inv",
                   "laplace_pdf", "laplace_rnd", "legend", "legendre",
                   "license", "line", "linkprop", "list_primes",
                   "loadaudio", "loadobj", "logistic_cdf",
                   "logistic_inv", "logistic_pdf", "logistic_rnd",
                   "logit", "loglog", "loglogerr", "logm", "logncdf",
                   "logninv", "lognpdf", "lognrnd", "logspace",
                   "lookfor", "ls_command", "lsqnonneg", "magic",
                   "mahalanobis", "manova", "matlabroot",
                   "mcnemar_test", "mean", "meansq", "median", "menu",
                   "mesh", "meshc", "meshgrid", "meshz", "mexext",
                   "mget", "mkpp", "mode", "moment", "movefile",
                   "mpoles", "mput", "namelengthmax", "nargchk",
                   "nargoutchk", "nbincdf", "nbininv", "nbinpdf",
                   "nbinrnd", "nchoosek", "ndgrid", "newplot", "news",
                   "nonzeros", "normcdf", "normest", "norminv",
                   "normpdf", "normrnd", "now", "nthroot", "null",
                   "ocean", "ols", "onenormest", "optimget",
                   "optimset", "orderfields", "orient", "orth",
                   "pack", "pareto", "parseparams", "pascal", "patch",
                   "pathdef", "pcg", "pchip", "pcolor", "pcr",
                   "peaks", "periodogram", "perl", "perms", "pie",
                   "pink", "planerot", "playaudio", "plot",
                   "plotmatrix", "plotyy", "poisscdf", "poissinv",
                   "poisspdf", "poissrnd", "polar", "poly",
                   "polyaffine", "polyarea", "polyderiv", "polyfit",
                   "polygcd", "polyint", "polyout", "polyreduce",
                   "polyval", "polyvalm", "postpad", "powerset",
                   "ppder", "ppint", "ppjumps", "ppplot", "ppval",
                   "pqpnonneg", "prepad", "primes", "print",
                   "print_usage", "prism", "probit", "qp", "qqplot",
                   "quadcc", "quadgk", "quadl", "quadv", "quiver",
                   "qzhess", "rainbow", "randi", "range", "rank",
                   "ranks", "rat", "reallog", "realpow", "realsqrt",
                   "record", "rectangle_lw", "rectangle_sw",
                   "rectint", "refresh", "refreshdata",
                   "regexptranslate", "repmat", "residue", "ribbon",
                   "rindex", "roots", "rose", "rosser", "rotdim",
                   "rref", "run", "run_count", "rundemos", "run_test",
                   "runtests", "saveas", "saveaudio", "saveobj",
                   "savepath", "scatter", "secd", "semilogx",
                   "semilogxerr", "semilogy", "semilogyerr",
                   "setaudio", "setdiff", "setfield", "setxor",
                   "shading", "shift", "shiftdim", "sign_test",
                   "sinc", "sind", "sinetone", "sinewave", "skewness",
                   "slice", "sombrero", "sortrows", "spaugment",
                   "spconvert", "spdiags", "spearman", "spectral_adf",
                   "spectral_xdf", "specular", "speed", "spencer",
                   "speye", "spfun", "sphere", "spinmap", "spline",
                   "spones", "sprand", "sprandn", "sprandsym",
                   "spring", "spstats", "spy", "sqp", "stairs",
                   "statistics", "std", "stdnormal_cdf",
                   "stdnormal_inv", "stdnormal_pdf", "stdnormal_rnd",
                   "stem", "stft", "strcat", "strchr", "strjust",
                   "strmatch", "strread", "strsplit", "strtok",
                   "strtrim", "strtrunc", "structfun", "studentize",
                   "subplot", "subsindex", "subspace", "substr",
                   "substruct", "summer", "surf", "surface", "surfc",
                   "surfl", "surfnorm", "svds", "swapbytes",
                   "sylvester_matrix", "symvar", "synthesis", "table",
                   "tand", "tar", "tcdf", "tempdir", "tempname",
                   "test", "text", "textread", "textscan", "tinv",
                   "title", "toeplitz", "tpdf", "trace", "trapz",
                   "treelayout", "treeplot", "triangle_lw",
                   "triangle_sw", "tril", "trimesh", "triplequad",
                   "triplot", "trisurf", "triu", "trnd", "tsearchn",
                   "t_test", "t_test_regression", "type", "unidcdf",
                   "unidinv", "unidpdf", "unidrnd", "unifcdf",
                   "unifinv", "unifpdf", "unifrnd", "union", "unique",
                   "unix", "unmkpp", "unpack", "untabify", "untar",
                   "unwrap", "unzip", "u_test", "validatestring",
                   "vander", "var", "var_test", "vech", "ver",
                   "version", "view", "voronoi", "voronoin",
                   "waitforbuttonpress", "wavread", "wavwrite",
                   "wblcdf", "wblinv", "wblpdf", "wblrnd", "weekday",
                   "welch_test", "what", "white", "whitebg",
                   "wienrnd", "wilcoxon_test", "wilkinson", "winter",
                   "xlabel", "xlim", "ylabel", "yulewalker", "zip",
                   "zlabel", "z_test", ]

    loadable_kw = [ "airy", "amd", "balance", "besselh", "besseli",
                   "besselj", "besselk", "bessely", "bitpack",
                   "bsxfun", "builtin", "ccolamd", "cellfun",
                   "cellslices", "chol", "choldelete", "cholinsert",
                   "cholinv", "cholshift", "cholupdate", "colamd",
                   "colloc", "convhulln", "convn", "csymamd",
                   "cummax", "cummin", "daspk", "daspk_options",
                   "dasrt", "dasrt_options", "dassl", "dassl_options",
                   "dbclear", "dbdown", "dbstack", "dbstatus",
                   "dbstop", "dbtype", "dbup", "dbwhere", "det",
                   "dlmread", "dmperm", "dot", "eig", "eigs",
                   "endgrent", "endpwent", "etree", "fft", "fftn",
                   "fftw", "filter", "find", "full", "gcd",
                   "getgrent", "getgrgid", "getgrnam", "getpwent",
                   "getpwnam", "getpwuid", "getrusage", "givens",
                   "gmtime", "gnuplot_binary", "hess", "ifft",
                   "ifftn", "inv", "isdebugmode", "issparse", "kron",
                   "localtime", "lookup", "lsode", "lsode_options",
                   "lu", "luinc", "luupdate", "matrix_type", "max",
                   "min", "mktime", "pinv", "qr", "qrdelete",
                   "qrinsert", "qrshift", "qrupdate", "quad",
                   "quad_options", "qz", "rand", "rande", "randg",
                   "randn", "randp", "randperm", "rcond", "regexp",
                   "regexpi", "regexprep", "schur", "setgrent",
                   "setpwent", "sort", "spalloc", "sparse", "spparms",
                   "sprank", "sqrtm", "strfind", "strftime",
                   "strptime", "strrep", "svd", "svd_driver", "syl",
                   "symamd", "symbfact", "symrcm", "time", "tsearch",
                   "typecast", "urlread", "urlwrite", ]

    mapping_kw = [ "abs", "acos", "acosh", "acot", "acoth", "acsc",
                  "acsch", "angle", "arg", "asec", "asech", "asin",
                  "asinh", "atan", "atanh", "beta", "betainc",
                  "betaln", "bincoeff", "cbrt", "ceil", "conj", "cos",
                  "cosh", "cot", "coth", "csc", "csch", "erf", "erfc",
                  "erfcx", "erfinv", "exp", "finite", "fix", "floor",
                  "fmod", "gamma", "gammainc", "gammaln", "imag",
                  "isalnum", "isalpha", "isascii", "iscntrl",
                  "isdigit", "isfinite", "isgraph", "isinf",
                  "islower", "isna", "isnan", "isprint", "ispunct",
                  "isspace", "isupper", "isxdigit", "lcm", "lgamma",
                  "log", "lower", "mod", "real", "rem", "round",
                  "roundb", "sec", "sech", "sign", "sin", "sinh",
                  "sqrt", "tan", "tanh", "toascii", "tolower", "xor",
                  ]

    builtin_consts = [ "EDITOR", "EXEC_PATH", "I", "IMAGE_PATH", "NA",
                   "OCTAVE_HOME", "OCTAVE_VERSION", "PAGER",
                   "PAGER_FLAGS", "SEEK_CUR", "SEEK_END", "SEEK_SET",
                   "SIG", "S_ISBLK", "S_ISCHR", "S_ISDIR", "S_ISFIFO",
                   "S_ISLNK", "S_ISREG", "S_ISSOCK", "WCONTINUE",
                   "WCOREDUMP", "WEXITSTATUS", "WIFCONTINUED",
                   "WIFEXITED", "WIFSIGNALED", "WIFSTOPPED", "WNOHANG",
                   "WSTOPSIG", "WTERMSIG", "WUNTRACED", ]

    tokens = {
        'root': [
            #We should look into multiline comments
            (r'[%#].*$', Comment),
            (r'^\s*function', Keyword, 'deffunc'),

            # from 'iskeyword' on hg changeset 8cc154f45e37
            (r'(__FILE__|__LINE__|break|case|catch|classdef|continue|do|else|'
             r'elseif|end|end_try_catch|end_unwind_protect|endclassdef|'
             r'endevents|endfor|endfunction|endif|endmethods|endproperties|'
             r'endswitch|endwhile|events|for|function|get|global|if|methods|'
             r'otherwise|persistent|properties|return|set|static|switch|try|'
             r'until|unwind_protect|unwind_protect_cleanup|while)\b', Keyword),

            ("(" + "|".join(  builtin_kw + command_kw
                            + function_kw + loadable_kw
                            + mapping_kw) + r')\b',  Name.Builtin),

            ("(" + "|".join(builtin_consts) + r')\b', Name.Constant),

            # operators in Octave but not Matlab:
            (r'-=|!=|!|/=|--', Operator),
            # operators:
            (r'-|==|~=|<|>|<=|>=|&&|&|~|\|\|?', Operator),
            # operators in Octave but not Matlab requiring escape for re:
            (r'\*=|\+=|\^=|\/=|\\=|\*\*|\+\+|\.\*\*',Operator),
            # operators requiring escape for re:
            (r'\.\*|\*|\+|\.\^|\.\\|\.\/|\/|\\', Operator),


            # punctuation:
            (r'\[|\]|\(|\)|\{|\}|:|@|\.|,', Punctuation),
            (r'=|:|;', Punctuation),

            (r'"[^"]*"', String),

            # quote can be transpose, instead of string:
            # (not great, but handles common cases...)
            (r'(?<=[\w\)\]])\'', Operator),
            (r'(?<![\w\)\]])\'', String, 'string'),

            ('[a-zA-Z_][a-zA-Z0-9_]*', Name),
            (r'.', Text),
        ],
        'string': [
            (r"[^']*'", String, '#pop'),
        ],
        'deffunc': [
            (r'(\s*)(?:(.+)(\s*)(=)(\s*))?(.+)(\()(.*)(\))(\s*)',
             bygroups(Text.Whitespace, Text, Text.Whitespace, Punctuation,
                      Text.Whitespace, Name.Function, Punctuation, Text,
                      Punctuation, Text.Whitespace), '#pop'),
        ],
    }

    def analyse_text(text):
        if re.match('^\s*[%#]', text, re.M): #Comment
            return 0.9
        return 0.1


class ScilabLexer(RegexLexer):
    """
    For Scilab source code.

    *New in Pygments 1.5.*
    """
    name = 'Scilab'
    aliases = ['scilab']
    filenames = ['*.sci', '*.sce', '*.tst']
    mimetypes = ['text/scilab']

    tokens = {
        'root': [
            (r'//.*?$', Comment.Single),
            (r'^\s*function', Keyword, 'deffunc'),

            (r'(__FILE__|__LINE__|break|case|catch|classdef|continue|do|else|'
             r'elseif|end|end_try_catch|end_unwind_protect|endclassdef|'
             r'endevents|endfor|endfunction|endif|endmethods|endproperties|'
             r'endswitch|endwhile|events|for|function|get|global|if|methods|'
             r'otherwise|persistent|properties|return|set|static|switch|try|'
             r'until|unwind_protect|unwind_protect_cleanup|while)\b', Keyword),

            ("(" + "|".join(_scilab_builtins.functions_kw +
                            _scilab_builtins.commands_kw +
                            _scilab_builtins.macros_kw
                            ) + r')\b',  Name.Builtin),

            (r'(%s)\b' % "|".join(map(re.escape, _scilab_builtins.builtin_consts)),
             Name.Constant),

            # operators:
            (r'-|==|~=|<|>|<=|>=|&&|&|~|\|\|?', Operator),
            # operators requiring escape for re:
            (r'\.\*|\*|\+|\.\^|\.\\|\.\/|\/|\\', Operator),

            # punctuation:
            (r'[\[\](){}@.,=:;]', Punctuation),

            (r'"[^"]*"', String),

            # quote can be transpose, instead of string:
            # (not great, but handles common cases...)
            (r'(?<=[\w\)\]])\'', Operator),
            (r'(?<![\w\)\]])\'', String, 'string'),

            ('[a-zA-Z_][a-zA-Z0-9_]*', Name),
            (r'.', Text),
        ],
        'string': [
            (r"[^']*'", String, '#pop'),
            (r'.', String, '#pop'),
        ],
        'deffunc': [
            (r'(\s*)(?:(.+)(\s*)(=)(\s*))?(.+)(\()(.*)(\))(\s*)',
             bygroups(Text.Whitespace, Text, Text.Whitespace, Punctuation,
                      Text.Whitespace, Name.Function, Punctuation, Text,
                      Punctuation, Text.Whitespace), '#pop'),
        ],
    }


class NumPyLexer(PythonLexer):
    """
    A Python lexer recognizing Numerical Python builtins.

    *New in Pygments 0.10.*
    """

    name = 'NumPy'
    aliases = ['numpy']

    # override the mimetypes to not inherit them from python
    mimetypes = []
    filenames = []

    EXTRA_KEYWORDS = set([
        'abs', 'absolute', 'accumulate', 'add', 'alen', 'all', 'allclose',
        'alltrue', 'alterdot', 'amax', 'amin', 'angle', 'any', 'append',
        'apply_along_axis', 'apply_over_axes', 'arange', 'arccos', 'arccosh',
        'arcsin', 'arcsinh', 'arctan', 'arctan2', 'arctanh', 'argmax', 'argmin',
        'argsort', 'argwhere', 'around', 'array', 'array2string', 'array_equal',
        'array_equiv', 'array_repr', 'array_split', 'array_str', 'arrayrange',
        'asanyarray', 'asarray', 'asarray_chkfinite', 'ascontiguousarray',
        'asfarray', 'asfortranarray', 'asmatrix', 'asscalar', 'astype',
        'atleast_1d', 'atleast_2d', 'atleast_3d', 'average', 'bartlett',
        'base_repr', 'beta', 'binary_repr', 'bincount', 'binomial',
        'bitwise_and', 'bitwise_not', 'bitwise_or', 'bitwise_xor', 'blackman',
        'bmat', 'broadcast', 'byte_bounds', 'bytes', 'byteswap', 'c_',
        'can_cast', 'ceil', 'choose', 'clip', 'column_stack', 'common_type',
        'compare_chararrays', 'compress', 'concatenate', 'conj', 'conjugate',
        'convolve', 'copy', 'corrcoef', 'correlate', 'cos', 'cosh', 'cov',
        'cross', 'cumprod', 'cumproduct', 'cumsum', 'delete', 'deprecate',
        'diag', 'diagflat', 'diagonal', 'diff', 'digitize', 'disp', 'divide',
        'dot', 'dsplit', 'dstack', 'dtype', 'dump', 'dumps', 'ediff1d', 'empty',
        'empty_like', 'equal', 'exp', 'expand_dims', 'expm1', 'extract', 'eye',
        'fabs', 'fastCopyAndTranspose', 'fft', 'fftfreq', 'fftshift', 'fill',
        'finfo', 'fix', 'flat', 'flatnonzero', 'flatten', 'fliplr', 'flipud',
        'floor', 'floor_divide', 'fmod', 'frexp', 'fromarrays', 'frombuffer',
        'fromfile', 'fromfunction', 'fromiter', 'frompyfunc', 'fromstring',
        'generic', 'get_array_wrap', 'get_include', 'get_numarray_include',
        'get_numpy_include', 'get_printoptions', 'getbuffer', 'getbufsize',
        'geterr', 'geterrcall', 'geterrobj', 'getfield', 'gradient', 'greater',
        'greater_equal', 'gumbel', 'hamming', 'hanning', 'histogram',
        'histogram2d', 'histogramdd', 'hsplit', 'hstack', 'hypot', 'i0',
        'identity', 'ifft', 'imag', 'index_exp', 'indices', 'inf', 'info',
        'inner', 'insert', 'int_asbuffer', 'interp', 'intersect1d',
        'intersect1d_nu', 'inv', 'invert', 'iscomplex', 'iscomplexobj',
        'isfinite', 'isfortran', 'isinf', 'isnan', 'isneginf', 'isposinf',
        'isreal', 'isrealobj', 'isscalar', 'issctype', 'issubclass_',
        'issubdtype', 'issubsctype', 'item', 'itemset', 'iterable', 'ix_',
        'kaiser', 'kron', 'ldexp', 'left_shift', 'less', 'less_equal', 'lexsort',
        'linspace', 'load', 'loads', 'loadtxt', 'log', 'log10', 'log1p', 'log2',
        'logical_and', 'logical_not', 'logical_or', 'logical_xor', 'logspace',
        'lstsq', 'mat', 'matrix', 'max', 'maximum', 'maximum_sctype',
        'may_share_memory', 'mean', 'median', 'meshgrid', 'mgrid', 'min',
        'minimum', 'mintypecode', 'mod', 'modf', 'msort', 'multiply', 'nan',
        'nan_to_num', 'nanargmax', 'nanargmin', 'nanmax', 'nanmin', 'nansum',
        'ndenumerate', 'ndim', 'ndindex', 'negative', 'newaxis', 'newbuffer',
        'newbyteorder', 'nonzero', 'not_equal', 'obj2sctype', 'ogrid', 'ones',
        'ones_like', 'outer', 'permutation', 'piecewise', 'pinv', 'pkgload',
        'place', 'poisson', 'poly', 'poly1d', 'polyadd', 'polyder', 'polydiv',
        'polyfit', 'polyint', 'polymul', 'polysub', 'polyval', 'power', 'prod',
        'product', 'ptp', 'put', 'putmask', 'r_', 'randint', 'random_integers',
        'random_sample', 'ranf', 'rank', 'ravel', 'real', 'real_if_close',
        'recarray', 'reciprocal', 'reduce', 'remainder', 'repeat', 'require',
        'reshape', 'resize', 'restoredot', 'right_shift', 'rint', 'roll',
        'rollaxis', 'roots', 'rot90', 'round', 'round_', 'row_stack', 's_',
        'sample', 'savetxt', 'sctype2char', 'searchsorted', 'seed', 'select',
        'set_numeric_ops', 'set_printoptions', 'set_string_function',
        'setbufsize', 'setdiff1d', 'seterr', 'seterrcall', 'seterrobj',
        'setfield', 'setflags', 'setmember1d', 'setxor1d', 'shape',
        'show_config', 'shuffle', 'sign', 'signbit', 'sin', 'sinc', 'sinh',
        'size', 'slice', 'solve', 'sometrue', 'sort', 'sort_complex', 'source',
        'split', 'sqrt', 'square', 'squeeze', 'standard_normal', 'std',
        'subtract', 'sum', 'svd', 'swapaxes', 'take', 'tan', 'tanh', 'tensordot',
        'test', 'tile', 'tofile', 'tolist', 'tostring', 'trace', 'transpose',
        'trapz', 'tri', 'tril', 'trim_zeros', 'triu', 'true_divide', 'typeDict',
        'typename', 'uniform', 'union1d', 'unique', 'unique1d', 'unravel_index',
        'unwrap', 'vander', 'var', 'vdot', 'vectorize', 'view', 'vonmises',
        'vsplit', 'vstack', 'weibull', 'where', 'who', 'zeros', 'zeros_like'
    ])

    def get_tokens_unprocessed(self, text):
        for index, token, value in \
                PythonLexer.get_tokens_unprocessed(self, text):
            if token is Name and value in self.EXTRA_KEYWORDS:
                yield index, Keyword.Pseudo, value
            else:
                yield index, token, value


class RConsoleLexer(Lexer):
    """
    For R console transcripts or R CMD BATCH output files.
    """

    name = 'RConsole'
    aliases = ['rconsole', 'rout']
    filenames = ['*.Rout']

    def get_tokens_unprocessed(self, text):
        slexer = SLexer(**self.options)

        current_code_block = ''
        insertions = []

        for match in line_re.finditer(text):
            line = match.group()
            if line.startswith('>') or line.startswith('+'):
                # Colorize the prompt as such,
                # then put rest of line into current_code_block
                insertions.append((len(current_code_block),
                                   [(0, Generic.Prompt, line[:2])]))
                current_code_block += line[2:]
            else:
                # We have reached a non-prompt line!
                # If we have stored prompt lines, need to process them first.
                if current_code_block:
                    # Weave together the prompts and highlight code.
                    for item in do_insertions(insertions,
                          slexer.get_tokens_unprocessed(current_code_block)):
                        yield item
                    # Reset vars for next code block.
                    current_code_block = ''
                    insertions = []
                # Now process the actual line itself, this is output from R.
                yield match.start(), Generic.Output, line

        # If we happen to end on a code block with nothing after it, need to
        # process the last code block. This is neither elegant nor DRY so
        # should be changed.
        if current_code_block:
            for item in do_insertions(insertions,
                    slexer.get_tokens_unprocessed(current_code_block)):
                yield item


class SLexer(RegexLexer):
    """
    For S, S-plus, and R source code.

    *New in Pygments 0.10.*
    """

    name = 'S'
    aliases = ['splus', 's', 'r']
    filenames = ['*.S', '*.R']
    mimetypes = ['text/S-plus', 'text/S', 'text/R']

    tokens = {
        'comments': [
            (r'#.*$', Comment.Single),
        ],
        'valid_name': [
            (r'[a-zA-Z][0-9a-zA-Z\._]+', Text),
            # can begin with ., but not if that is followed by a digit
            (r'\.[a-zA-Z_][0-9a-zA-Z\._]+', Text),
        ],
        'punctuation': [
            (r'\[{1,2}|\]{1,2}|\(|\)|;|,', Punctuation),
        ],
        'keywords': [
            (r'(if|else|for|while|repeat|in|next|break|return|switch|function)'
             r'(?![0-9a-zA-Z\._])',
             Keyword.Reserved)
        ],
        'operators': [
            (r'<<?-|->>?|-|==|<=|>=|<|>|&&?|!=|\|\|?|\?', Operator),
            (r'\*|\+|\^|/|!|%[^%]*%|=|~|\$|@|:{1,3}', Operator)
        ],
        'builtin_symbols': [
            (r'(NULL|NA(_(integer|real|complex|character)_)?|'
             r'Inf|TRUE|FALSE|NaN|\.\.(\.|[0-9]+))'
             r'(?![0-9a-zA-Z\._])',
             Keyword.Constant),
            (r'(T|F)\b', Keyword.Variable),
        ],
        'numbers': [
            # hex number
            (r'0[xX][a-fA-F0-9]+([pP][0-9]+)?[Li]?', Number.Hex),
            # decimal number
            (r'[+-]?([0-9]+(\.[0-9]+)?|\.[0-9]+)([eE][+-]?[0-9]+)?[Li]?',
             Number),
        ],
        'statements': [
            include('comments'),
            # whitespaces
            (r'\s+', Text),
            (r'`.*?`', String.Backtick),
            (r'\'', String, 'string_squote'),
            (r'\"', String, 'string_dquote'),
            include('builtin_symbols'),
            include('numbers'),
            include('keywords'),
            include('punctuation'),
            include('operators'),
            include('valid_name'),
        ],
        'root': [
            include('statements'),
            # blocks:
            (r'\{|\}', Punctuation),
            #(r'\{', Punctuation, 'block'),
            (r'.', Text),
        ],
        #'block': [
        #    include('statements'),
        #    ('\{', Punctuation, '#push'),
        #    ('\}', Punctuation, '#pop')
        #],
        'string_squote': [
            (r'([^\'\\]|\\.)*\'', String, '#pop'),
        ],
        'string_dquote': [
            (r'([^"\\]|\\.)*"', String, '#pop'),
        ],
    }

    def analyse_text(text):
        return '<-' in text
