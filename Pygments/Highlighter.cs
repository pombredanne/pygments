﻿using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using IronPython.Hosting;

namespace Pygments
{
    public class Highlighter
    {
        static Highlighter()
        {
            // allows assemblies to be stored in the any assembly as a resource.
            // much more flexible than other people's :D
            AppDomain.CurrentDomain.AssemblyResolve += (sender, args) => {

                var match = new AssemblyName(args.Name).Name + ".dll";

                foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies()) {
                    try {
                        foreach (var resource in assembly.GetManifestResourceNames()) {
                            if (resource.Equals(match, StringComparison.InvariantCultureIgnoreCase)) {
                                using (var stream = assembly.GetManifestResourceStream(resource)) {
                                    var assemblyData = new Byte[stream.Length];
                                    stream.Read(assemblyData, 0, assemblyData.Length);
                                    return Assembly.Load(assemblyData);
                                }
                            }
                        }
                    }
                    catch {

                    }
                }
                return null;

            };
        }

        public class Lexer
        {
            public string Name { get; internal set; }
            public IEnumerable<string> Aliases { get; internal set; }
            public IEnumerable<string> Filemasks { get; internal set; }
            public IEnumerable<string> MediaTypes { get; internal set; }
        }

        public class Style
        {
            public string Name { get; internal set; }
            internal dynamic obj { get; set; }
        }

        private  dynamic _highlight;
        private  dynamic _formatters;
        private  dynamic _lexers;
        private  dynamic _styles;

        public static IEnumerable<Lexer> Lexers;
        public static IEnumerable<string> Styles;

        public Highlighter()
        {
            if (_highlight == null)
            {
                var ipy = Python.CreateRuntime();
                dynamic clr = ipy.GetClrModule();
                clr.AddReference("pygments");

                _lexers = ipy.Import("pygments.lexers").lexers;
                Lexers = ((IEnumerable) _lexers.get_all_lexers()).Cast<object>().Select(each =>
                {
                    dynamic e = each;
                    return new Lexer
                    {
                        Name = e[0],
                        Aliases = ((IEnumerable<object>) (e[1])).Select(i => i.ToString()).ToArray(),
                        Filemasks = ((IEnumerable<object>) (e[2])).Select(i => i.ToString()).ToArray(),
                        MediaTypes = ((IEnumerable<object>) (e[3])).Select(i => i.ToString()).ToArray(),
                    };
                }).ToArray();

                _styles = ipy.Import("pygments.styles").styles;
                Styles =
                    ((IEnumerable) _styles.get_all_styles()).Cast<object>().Select(each => each.ToString()).ToArray();

                _highlight = ipy.Import("pygments").highlight;
                _formatters = ipy.Import("pygments.formatters").formatters;
            }
            
        }

        private dynamic GetLexerByName(string name)
        {
            return _lexers.get_lexer_by_name(name);
        }

        private dynamic GetLexerForFilename(string filename)
        {
            return _lexers.get_lexer_for_filename(filename);
        }

        private dynamic GetLexerForMediaType(string mediaType)
        {
            return _lexers.get_lexer_for_mimetype(mediaType);
        }

        private dynamic GetStyleByName(string name)
        {
            return _styles.get_style_by_name(name);
        }

        public string HighlightToBBCode(string sourceCode, string lexerName, string styleName, bool codeTag = false, bool  monoFont = false ) {
            return _highlight(sourceCode, GetLexerByName(lexerName),
                _formatters.BBCodeFormatter(style: GetStyleByName(styleName), codetag:codeTag, monofont:monoFont));
        }

        public string HighlightToRTF(string sourceCode, string lexerName, string styleName, string fontFace=null) {
            return _highlight(sourceCode, GetLexerByName(lexerName),
                _formatters.RtfFormatter(style: GetStyleByName(styleName), fontface: fontFace));
        }

        public string HighlightToHtml(string sourceCode, string lexerName, string styleName, bool fragment = false, string title = "", bool generateInlineStyles = false, string classPrefix = "", 
            string wrappingDivClass = "highlight", string wrappingDivStyles = "", string preStyles = "", LineNumberStyle lineNumberStyle = LineNumberStyle.none, int lineNumberStart = 1, bool noBackground = false,  string lineBreaks="\n", string lineAnchorPrefix = null, string lineSpanPrefix = null, bool anchorLineNumbers = false, string highlightLines = "")
        {
            return _highlight(sourceCode, GetLexerByName(lexerName),
                _formatters.HtmlFormatter(style: GetStyleByName(styleName), full: !fragment, title: title, noclasses: generateInlineStyles, classprefix: classPrefix, cssclass: wrappingDivClass, cssstyles: wrappingDivStyles, prestyles: preStyles, linenos: lineNumberStyle.ToString().Replace("none",""), linenostart: lineNumberStart, nobackground: noBackground, lineseparator: lineBreaks, lineanchors: lineAnchorPrefix, linespans: lineSpanPrefix, anchorlinenos: anchorLineNumbers, hl_lines:highlightLines));
        }

        public string HighlightToLatex(string sourceCode, string lexerName, string styleName, bool fragment = false, string title = "", string documentClass = "article", bool lineNumbers = false, int lineNumberStart = 1, int lineStep = 1, bool texComments = false, bool mathEscape = false ) {
            return _highlight(sourceCode, GetLexerByName(lexerName),
                _formatters.LatexFormatter(style: GetStyleByName(styleName), full: !fragment, title:title, docclass:documentClass, linenos:lineNumbers, linenostart:lineNumberStart, linenostep:lineStep, texcomments:texComments, mathescape:mathEscape));
        }
    }
}