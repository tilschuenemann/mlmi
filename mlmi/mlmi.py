from langdetect import DetectorFactory, LangDetectException, detect
import pandas as pd
import pymediainfo
import tqdm

import argparse
import json
import glob
import pathlib


def get_subtitle_data(input_path: str, sub_exts: list[str]) -> pd.DataFrame:
    """

    Parameters
    -------
    input_path: str
        directory to scan for subtitles
    sub_exts: list[str]
        list of subtitle extensions to scan for

    Returns
    -------
    pd.DataFrame
        df with movie folder and subtitles column. One folder with many
        subtitles has one row.

    """
    DetectorFactory.seed = 0

    files = []
    for ext in sub_exts:
        subs = glob.glob(input_path + f"*/*{ext}", recursive=True)
        files.extend(subs)

    df = pd.DataFrame()

    for sub in tqdm.tqdm(files, "Subtitles"):
        with open(sub, "r", errors="ignore") as f:
            content_list = f.readlines()

        content = "".join(content_list)
        try:
            lang = detect(content)
        except LangDetectException:
            lang = "no valid subs"

        tmp = pd.DataFrame(
            {
                "parent": [str(pathlib.Path(sub).parent)],
                "subtitle_files": [lang],
            }
        )
        df = pd.concat([df, tmp], axis=0)

    df = df.groupby(["parent"]).agg({"subtitle_files": ",".join})
    df = df.reset_index()
    return df


def get_mediainfo(
    input_folder: str, mov_exts: list[str], output_folder: str = ""
) -> dict[str, pd.DataFrame]:
    """

    Parameters
    -------
    input_folder: str
        folder to
    mov_exts: list[str]
        list of video file extensions

    Returns
    -------
    pd.DataFrame

    """
    files = []
    for ext in mov_exts:
        tmp = glob.glob(input_folder + f"*/*{ext}", recursive=True)
        files.extend(tmp)

    videos = pd.DataFrame()
    audios = pd.DataFrame()
    subs = pd.DataFrame()
    generals = pd.DataFrame()

    for item in tqdm.tqdm(files, desc="Movies   "):

        m_info = pymediainfo.MediaInfo.parse(item, output="JSON")
        m_info = json.loads(m_info)

        tmp1 = pd.DataFrame().from_dict({"item": [item]})

        for track in m_info["media"]["track"]:

            tmp2 = pd.json_normalize(track)
            tmp = pd.concat([tmp1, tmp2], axis=1)

            if track["@type"] == "General":
                generals = pd.concat([generals, tmp], axis=0)
            elif track["@type"] == "Video":
                videos = pd.concat([videos, tmp], axis=0)
            elif track["@type"] == "Audio":
                audios = pd.concat([audios, tmp], axis=0)
            elif track["@type"] == "Text":
                subs = pd.concat([subs, tmp], axis=0)

    outputs = {"general": generals, "video": videos, "audio": audios, "subtitles": subs}

    WRITE = True
    if output_folder == "":
        WRITE = False

    if pathlib.Path(output_folder).exists() is False and WRITE:
        output_folder = str(pathlib.Path(__file__).parent)

    if WRITE:
        for name, df in outputs.items():
            df.to_csv(
                f"{output_folder}/{name}.csv", index=False, sep=";", encoding="UTF-8"
            )

    return outputs


def _list_langs(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function for aggregating the language column by joining its items."""
    tmp = df[["item", "Language"]].copy()
    tmp["parent"] = [pathlib.Path(x).parent for x in df["item"]]
    tmp = tmp.astype({"Language": str, "parent": str})
    tmp.drop("item", axis=1, inplace=True)
    tmp = tmp.groupby(["parent"]).agg({"Language": ",".join})
    return tmp


def get_language_overview(
    input_folder: str, mov_exts: list[str], sub_exts: list[str]
) -> pd.DataFrame:
    output = get_mediainfo(input_folder, mov_exts)
    audio = output["audio"][["Language", "item"]]
    subs = output["subtitles"][["Language", "item"]]

    audio = _list_langs(audio)
    subs = _list_langs(subs)

    files = pd.DataFrame(pathlib.Path(input_folder).iterdir(), columns=["parent"])
    files["parent"] = files["parent"].astype(str)

    files = files.merge(audio, on="parent", how="left", suffixes=("", ".audio"))
    files = files.merge(subs, on="parent", how="left", suffixes=("", ".subtitles"))
    files.columns = ["parent", "audio", "subtitles"]

    files["audio"] = files["audio"].fillna("")
    files["audio"] = files["audio"].str.replace(r".?nan", "", regex=True)
    files["subtitles"] = files["subtitles"].fillna("")

    return files


def main(
    input_folder: str, mov_exts, sub_exts, output_folder: str = ""
) -> pd.DataFrame:

    mediainfo = get_language_overview(input_folder, mov_exts, sub_exts)
    subtitle_files = get_subtitle_data(input_folder, sub_exts)
    df = mediainfo.merge(subtitle_files, on="parent", how="left")
    df["subtitle_files"] = df["subtitle_files"].fillna("")
    df = df.sort_values("parent")

    WRITE = True
    if output_folder == "":
        WRITE = False
    if pathlib.Path(output_folder).exists() is False and WRITE:
        output_folder = str(pathlib.Path(__file__).parent)

    if WRITE:
        df.to_csv(f"{output_folder}/mmmi.csv", sep=";", index=False, encoding="UTF-8")
    return df


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("--i", help="input folder", type=str, dest="i")
    arg.add_argument("--o", help="output folder", type=str, dest="o", required=False)
    arg.add_argument("--m", help="file extension for movies", nargs="+", dest="m")
    arg.add_argument("--s", help="file extensions for subtitles", nargs="+", dest="s")

    args = arg.parse_args()

    main(input_folder=args.i, mov_exts=args.m, sub_exts=args.s, output_folder=args.o)
