import os
import re
from pathlib import Path

GITHUB_URL = r"https://github.com/seleniumbase/SeleniumBase/blob/master/"
ROOT_DIR = Path(__file__).parents[1]
URL_PATTERN = re.compile(
    r"(?:\(|<a href=\")(?P<url>{}[\w/.]+\.md)(?:\)|\")".format(GITHUB_URL)
)
MD_PATH_PATTERN = re.compile(r"\[.*\]\((?P<path>[\w\\._/]+\.md)\)")
HEADER_PATTERN = re.compile(
    r"^(?P<level>#+)\s*(<[\w\s=\":/.]+>)?\s*\**(?P<header>.*[\w`]):?\**\s*$",
    flags=re.MULTILINE,
)

PROCESSED_PATHS = set()


def normalize_path(path):
    path = Path(path).absolute().relative_to(ROOT_DIR)
    return str(path).replace("\\", "/")


def read_file(file_name):
    path = ROOT_DIR / file_name
    with path.open() as file_handle:
        content = file_handle.read()
    return content


def process_file(file_name):
    content = read_file(file_name)
    urls = URL_PATTERN.findall(content)
    content = content.replace("<br />", "  \n")
    content = re.sub(HEADER_PATTERN, r"\g<level> \g<header>", content)
    directory = "/".join(normalize_path(file_name).split("/")[:-1])

    paths = set()

    md_paths = MD_PATH_PATTERN.findall(content)
    for md_path in md_paths:
        path = md_path.lstrip("/")
        if (ROOT_DIR / directory / path).exists():
            path = ROOT_DIR / directory / path
        else:
            path = ROOT_DIR / path
        path = path.resolve().relative_to(ROOT_DIR)
        paths.add(normalize_path(path))
        content = content.replace("(" + md_path + ")", normalize_path(path))

    for url in urls:
        path = url[len(GITHUB_URL):]
        paths.add(path)
        content = content.replace(
            url, normalize_path(os.path.relpath(path, directory))
        )

    output_path = ROOT_DIR / "docs" / file_name
    if not output_path.parent.is_dir():
        os.makedirs(output_path.parent)

    with output_path.open("w+") as output_file:
        output_file.write(content)
    PROCESSED_PATHS.add(normalize_path(file_name))

    for path in paths:
        if path not in PROCESSED_PATHS:
            process_file(normalize_path(path))


def main(*args, **kwargs):
    files_to_process = ["README.md"]
    for dir_ in os.listdir(ROOT_DIR / "help_docs"):
        files_to_process.append(os.path.join("help_docs", dir_))

    for file_ in files_to_process:
        process_file(file_)