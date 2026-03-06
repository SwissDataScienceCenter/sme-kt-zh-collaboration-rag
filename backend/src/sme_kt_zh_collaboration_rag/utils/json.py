from partial_json_parser import loads as partial_json_loads


def parse_llm_json_stream(input_str: str) -> dict[str, str] | None:
    try:
        opening_bracket_index = input_str.index("{")
        json_part = input_str[opening_bracket_index:]
        json_object = partial_json_loads(json_part)
        return json_object

    except ValueError as e:
        # TODO: Fix
        # This is a "hack" because the the string send by the llm could either skip the json formatting asked or be ````{ "conte...
        # So we'll consider that after 10 characters, if we didn't received the "{" then it's a plain string
        if len(input_str) > 10 and "substring not found" in str(e):
            return {"answer": input_str}
        return {}
