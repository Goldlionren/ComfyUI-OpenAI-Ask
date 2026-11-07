from .node_openai_ask import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .node_string_list import JRStringToList

NODE_CLASS_MAPPINGS["JRStringToList"] = JRStringToList
NODE_DISPLAY_NAME_MAPPINGS["JRStringToList"] = "JR Node: String to List (Dynamic)"

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
