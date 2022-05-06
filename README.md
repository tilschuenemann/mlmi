# mlmi: movielibrary-mediainfo

This program parses [mediainfo](https://mediaarea.net/en/MediaInfo) from
your movie library and checks subtitle file languages.

I created this to solve the following problems:
* What movies have subtitles and which don't?
* Which movies need to be replaced with a better quality version of it?
* What is the total runtime of my movie library?

## Usage
For this program to work, your movie library structure should look like this:
```
/movie_library
    /The Matrix (1999)
        The Matrix.mkv
    /The Matrix Reloaded (2003)
        The Matrix Reloaded.avi
        The Matrix Reloaded.srt
``` 

You can then use the main method to generate a CSV / dataframe where subtitle
and audio track languages will be listed, as well as subtitle file languages.

```python

import mlmi

input_folder = "/movie_library"
mov_exts = [".avi", ".mkv"]
sub_exts = [".srt"]
df = main(input_folder, mov_exts, sub_exts)
```

## get_mediainfo
get_mediainfo aggregates some mediainfo tracks (only "general", "video", "audio", "text")
into dataframes, which are stored in the resulting dict.

[Mediainfo specifications for different formats](https://mediaarea.net/en/MediaInfo/Support/Formats)

```python
import mlmi

input_folder = "/movie_library"
mov_exts = [".avi", ".mkv"]
sub_exts = [".srt"]

mediainfo_data = get_mediainfo(input_folder, mov_exts)
```

### get_subtitle_data
get_subtitle_data searches for all files with the supplied sub_exts in the input_folder,
parses their content and uses langdetect to map a language to each subtitle. 
Result is returned as dataframe.

```python
import mlmi

input_folder = "/movie_library"
sub_exts = [".srt"]

subtitle_data = get_subtitle_data(input_folder, sub_exts)
```

### get_language_overview
get_language_overview compiles a list of subtitle, audio and subtitle file languages and
maps them to the direct child directories of the input_folder. The result is returned as
a data frame.

```python
import mlmi

input_folder = "/movie_library"
sub_exts = [".srt"]

language_data = get_subtitle_data(input_folder, sub_exts)
```
