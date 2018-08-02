# re-regex

An experiment in making composable and friendly regular expressions.

## What's the idea?

Say you're parsing something like XML. You're looking for tags with some number of arguments, that might or might not be quoted. Example:

```
[b]Hello![/b]
[quote="bvisness" post = 123]Something I said![/quote]
```

The regular expression for an argument is moderately complex. It might look like this (in Python's expanded syntax):

```
(?P<name>[a-zA-Z]+)
(?:
    \s*=\s*
    (?:
        (?P<quote>'|")(?P<quoted_val>.*?)(?P=quote)
        |(?P<bare_val>[^\s\]]+)
    )
)?
```

Note the named groups (`?P<name>`), and in particular the named backreference (`?P=`) so we can see which type of quote we opened with.

Now say we want a regular expression that will recognize the whole tag. To really recognize the tag, you have to be able to recognize an argument. It might look like this overall, where you would replace `RE_ARG` with the entire above regex:

```\[\s*(?P<args>(?:RE_ARG)(?:\s+(?:RE_ARG))*)\s*\]```

But how do you actually sub in the regular expression for an argument? `RE_ARG` appears twice, so the named groups like `quoted_val` conflict, and Python won't let you do it. And if you remove names from RE_ARG, the named backreference won't work.

So how can we handle this problem intelligently?

Re-regex provides two main features:

1. A friendly and self-documenting interface for creating a regular expression, and
2. The ability to compose multiple regular expressions without losing names.

Re-regex provides a simple class that mimics Python's `re` module. It also provides several helpful functions like `wrap`, `maybe`, and `one_of` to help you build a re-regex in an intuitive way. All re-regex objects are composable and will never have conflicting names.

Here's what our above example looks like in re-regex:

```python
RE_ARG = wrap([
    name('arg_name', wrap(r'[a-zA-Z_-]+')),
    maybe([
        r'\s*=\s*',
        one_of([
            [
                name('quote', r'\'|"'),
                name('quoted_val', r'.*?'),
                backref('quote'),
            ],
            name('bare_val', r'[^\s\]]+'),
        ]),
    ]),
])

RE_TAG = wrap([
    r'\[\s*',
    RE_ARG,
    zero_or_more([
        r'\s+',
        RE_ARG,
    ]),
    r'\s*\]',
])

print(RE_ARG)
print(RE_TAG)

tag = '[quote = \'bvisness\' post=123 foo="bar" baz]'

tag_match = RE_TAG.search(tag)
if tag_match:
    for arg_match in RE_ARG.finditer(tag_match.group(0)):
        print(arg_match.group('arg_name'), arg_match.group('quoted_val'), arg_match.group('bare_val'))
        
# prints:
# quote bvisness None
# post None 123
# foo bar None
# baz None None
```

Re-regex enables you to build an entire library of small, easily understood regular expressions, then combine them to recognize more and more complex patterns, without it ever getting confusing or overwhelming.
