"""Dynamic STRING inputs combined into a ComfyUI execution list."""

import re

_INPUT_NAME = re.compile(r"text_([1-9][0-9]*)\Z")
_INPUT_SPEC = ("STRING", {"forceInput": True})


class _DynamicStringInputs(dict):
    """Accept text_N ports created by the frontend, without displaying all of them."""

    def __contains__(self, key):
        return super().__contains__(key) or (
            isinstance(key, str) and _INPUT_NAME.fullmatch(key) is not None
        )

    def __missing__(self, key):
        if isinstance(key, str) and _INPUT_NAME.fullmatch(key):
            return _INPUT_SPEC
        raise KeyError(key)


class JRStringToList:
    """Emit one STRING item per connected text_N input, in numeric port order."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": _DynamicStringInputs({"text_1": _INPUT_SPEC}),
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("list",)
    FUNCTION = "combine"
    CATEGORY = "🥷 Integrations/OpenAI"
    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True,)

    def combine(self, **kwargs):
        items = []
        numbered_inputs = sorted(
            ((int(match.group(1)), value) for name, value in kwargs.items()
             if (match := _INPUT_NAME.fullmatch(name)) is not None),
            key=lambda entry: entry[0],
        )
        for _, values in numbered_inputs:
            # INPUT_IS_LIST=True: ComfyUI passes each connected input as a list.
            # An upstream node may itself produce multiple STRING list items.
            for value in values:
                if not isinstance(value, str):
                    raise TypeError("JR String to List accepts STRING inputs only")
                items.append(value)
        return (items,)
