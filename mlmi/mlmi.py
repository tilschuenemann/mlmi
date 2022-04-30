from langdetect import DetectorFactory, LangDetectException, detect
import pandas as pd
import pymediainfo
import tqdm

import argparse
import json
import glob
import pathlib
import re


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
        subs = glob.glob(input_path + f"/**/*{ext}", recursive=True)
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
                "parent_folder": [str(pathlib.Path(sub).parent)],
                "subtitles.s": [lang],
            }
        )
        df = pd.concat([df, tmp], axis=0)

    df = df.groupby("parent_folder").agg({"subtitles.s": lambda x: list(x)})

    return df


def get_movie_data(input_folder: str, mov_exts: list[str]) -> pd.DataFrame:
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
        tmp = glob.glob(input_folder + f"/**/*{ext}", recursive=True)
        files.extend(tmp)

    df = pd.DataFrame()

    for item in tqdm.tqdm(files, "Movies   "):
        m_info = pymediainfo.MediaInfo.parse(item, output="JSON")
        m_info = json.loads(m_info)

        movie_data = pd.DataFrame.from_dict(
            {"file": [item], "parent_folder": [str(pathlib.Path(item).parent)]}
        )
        subtitles = []
        audio_tracks = []

        for track in m_info["media"]["track"]:
            if track["@type"] == "Video":

                tmp = pd.DataFrame.from_dict(
                    {
                        "bitrate": [track.get("BitRate")],
                        "height": [track.get("Height")],
                        "width": [track.get("Width")],
                        "display_ratio": [track.get("DisplayAspectRatio_String")],
                        "framerate": [str(track.get("FrameRate"))],
                    }
                )

                movie_data = pd.concat([movie_data, tmp], axis=1)

                audio_tracks.append(track.get("Language"))
                audio_tracks.append(track.get("Language_String"))
                audio_tracks.append(track.get("Language_String1"))
                audio_tracks.append(track.get("Language_String2"))
                audio_tracks.append(track.get("Language_String3"))
                audio_tracks.append(track.get("Language_String4"))

            elif track["@type"] == "Audio":

                audio_tracks.append(track.get("Language"))
                audio_tracks.append(track.get("Language_String"))
                audio_tracks.append(track.get("Language_String1"))
                audio_tracks.append(track.get("Language_String2"))
                audio_tracks.append(track.get("Language_String3"))
                audio_tracks.append(track.get("Language_String4"))

            elif track["@type"] == "General":

                audio_tracks.append(track.get("Video_Language_List"))
                audio_tracks.append(track.get("Audio_Language_List"))

            elif track["@type"] == "Text":

                sub = track.get("Language")
                sub = "noname" if sub == "" else sub

                subtitles.append(sub)

        audio_tracks = [
            x for x in audio_tracks if x is not None and re.match(r"^[A-Za-z]{2}$", x)
        ]
        audio_tracks = list(set(audio_tracks))

        movie_data["audio_tracks"] = str(audio_tracks)
        movie_data["subtitles.m"] = str(subtitles)
        df = pd.concat([df, movie_data], axis=0)

    return df


def main(
    input_folder: str, mov_exts, sub_exts, output_folder: str = ""
) -> pd.DataFrame:
    mov_data = get_movie_data(input_folder, mov_exts)
    sub_data = get_subtitle_data(input_folder, sub_exts)
    # df = mov_data.join(sub_data, on="parent_folder", how="left")
    df = mov_data.merge(sub_data, on="parent_folder", how="left")

    if pathlib.Path(output_folder).exists() is False or output_folder == "":
        output_folder = str(pathlib.Path(__file__).parent)

    df = df.sort_values("parent_folder")
    # df.to_csv(f"{output_folder}/mmmi.csv", sep=";", index=False, encoding="UTF-8")
    return df


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("--i", help="input folder", type=str, dest="i")
    arg.add_argument("--o", help="output folder", type=str, dest="o", required=False)
    arg.add_argument("--m", help="file extension for movies", nargs="+", dest="m")
    arg.add_argument("--s", help="file extensions for subtitles", nargs="+", dest="s")

    args = arg.parse_args()

    main(input_folder=args.i, mov_exts=args.m, sub_exts=args.s, output_folder=args.o)
