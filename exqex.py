#!/usr/bin/env python

# [  quote = 'delix' post=123 foo="bar" baz]

import re

# RE_ARG_S = r'''
#     (?P<name>[a-zA-Z]+)
#     (?:
#         \s*=\s*
#         (?:
#             '(?P<single_quoted_val>.*?)'
#             |"(?P<double_quoted_val>.*?)"
#             |(?P<bare_val>[^\s\]]+)
#         )
#     )?
# '''
# RE_TAG_S = r'\[\s*(?P<args>(?:' + strip_names(RE_ARG_S) + r')(?:\s+(?:' + strip_names(RE_ARG_S) + r'))*)\s*\]'


class RenderContext:
    def __init__(self):
        self.index = 0


class Match:
    def __init__(self, matched_string):
        self.matched_string = matched_string
        self.named_groups = {}

    def group(self, name):
        if name == 0:
            return self.matched_string

        return self.named_groups[name] or None


class Wrapper:
    def __init__(self, regex_like):
        self.wrapped = []

        try:
            for thing in regex_like:
                self.wrapped.append(thing)
        except TypeError:
            self.wrapped.append(regex_like)

    def __str__(self):
        return self.render()

    def render(self):
        context = RenderContext()
        return self.render_part(context)

    def render_part(self, context):
        index = context.index
        context.index += 1

        rendered = []
        for thing in self.wrapped:
            if isinstance(thing, NamedGroup):
                rendered.append(thing.render(index, context))
            elif isinstance(thing, Backref):
                rendered.append(thing.render(index))
            elif isinstance(thing, Wrapper):
                rendered.append(thing.render_part(context))
            else:
                rendered.append(thing)

        return '(?:' + ''.join(rendered) + ')'

    def search(self, string):
        re_string = self.render()
        m = re.search(re_string, string)

        if not m:
            return None

        result = Match(m.group(0))
        for name, text in m.groupdict().items():
            plain_name = re.sub(r'__\d+__$', '', name)
            result.named_groups[plain_name] = text

        return result

    def finditer(self, string):
        re_string = self.render()
        matches = re.finditer(re_string, string)

        result = []
        for match in matches:
            custom_match = Match(match.group(0))
            for name, text in match.groupdict().items():
                plain_name = re.sub(r'__\d+__$', '', name)
                custom_match.named_groups[plain_name] = text
            result.append(custom_match)

        return result


class NamedGroup:
    def __init__(self, name, wrapper):
        self.name = name
        self.wrapper = wrapper

    def render(self, index, context):
        return f'(?P<{self.name}__{index}__>{self.wrapper.render_part(context)})'


class Backref:
    def __init__(self, name):
        self.name = name

    def render(self, index):
        return f'(?P={self.name}__{index}__)'


def wrap(regex_like):
    return Wrapper(regex_like)

def maybe(regex_like):
    return Wrapper([Wrapper(regex_like), '?'])

def zero_or_more(regex_like):
    return Wrapper([Wrapper(regex_like), '*'])

def one_of(regex_likes):
    result = ['(?:']
    for i, thing in enumerate(regex_likes):
        if i > 0:
            result.append('|')
        result.append(Wrapper(thing))
    result.append(')')

    return Wrapper(result)

def name(name, regex_like):
    return NamedGroup(name, Wrapper(regex_like))

def backref(name):
    return Backref(name)


if __name__ == '__main__':
    tag = '[quote = \'delix\' post=123 foo="bar" baz]'
    args = [
        'quote = \'delix\'',
        'post=123',
        'foo="bar"',
        'baz',
    ]

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

    tag_match = RE_TAG.search(tag)
    if tag_match:
        for arg_match in RE_ARG.finditer(tag_match.group(0)):
            print(arg_match.group('arg_name'), arg_match.group('quoted_val'), arg_match.group('bare_val'))
