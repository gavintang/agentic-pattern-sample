import json
from typing import Any

from glab.comm.library import Tool

class ValidateJsonDataTool(Tool):
  def process(self, **params) -> dict[str, Any]:
    content = params.get('content')
    if not isinstance(content, str): raise ValueError("invalid 'content'")
    try:
      _json=json.loads(content)
      return _json if isinstance(_json, dict) else {"list": _json} if isinstance(_json, list) else {"input": _json}
    except json.JSONDecodeError as e:
      return {"input": content}
