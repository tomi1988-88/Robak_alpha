

def price_into_number(text):
    text = text.strip()
    ## pobawić się regexem
    if "," in text or "." in text:
        num = "".join([i if i.isdigit() else "." if i == "," or i == "." else "" for i in text])
    else:
        index = text.index(" ")
        text = text[:index] + "." + text[index:]
        num = "".join([i if i.isdigit() else "." if i == "," or i == "." else "" for i in text])
    try:
        num = float(num)
    except ValueError as e:
        num = f"price_into_numbers - {e}"
    return num


class WrongFormat(Exception):
    msg = {":": "Wrong format in Config file: no COLON in the line. Valid format eg. category: your_category"}


# class WrongArgument(Exception):
#     additional_args = ['href', 'is_available', 'wrong_bytes']
#     minimal_args = ['category', 'initial_link', 'n_pages',
#                      'offer_boxes', 'title', 'price_1']
#
#     msg = f"Looks like you missed something in the Config file. \nMinimal args are: {minimal_args} \nPossible args: {additional_args + ['price_2', 'price_3...']}"


def is_colon(text):
    if ":" not in text:
        raise WrongFormat(WrongFormat.msg.get(":"))
    else:
        return text


def input_validator(path):
    with open(path, "r", encoding="utf-8") as config:
        config = config.read().split("\n\n")

    config = [x.strip().split("\n") for x in config]
    config = [x for x in config if x != [""]]

    data = {}

    project_title = is_colon(config[0][0]).split(":", 1)
    project_title = {project_title[0]: project_title[1].strip()}
    data.update(project_title)

    for category_num, args in enumerate(config[1:]):
        args = {x[0]: x[1].strip() for x in [is_colon(x).split(":", 1) for x in args]}
        data.update({category_num: args})

    return data
