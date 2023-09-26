#!/usr/bin/env python

""""
Transcribes and summarizes a directory of audio or video files

You can use whisper in CLI mode or as a python module.

"""
import pathlib
import re
import click
import whisper
import time
import subprocess
import multiprocessing


def transcribe_file_cli(file, modelType="base.en", language="en"):
    """Transcribe a file using the CLI and return the result"""

    # get root directory of file
    root_dir = pathlib.Path(file).parent
    file_name_stem = pathlib.Path(file).stem
    file_type = pathlib.Path(file).suffix
    print(
        f"Working in: {root_dir} with file_name_stem: {file_name_stem} and extension: {file_type}"
    )
    # import ipdb; ipdb.set_trace()
    # write the transcribed file into the same directory
    output_file = f"{root_dir}/{file_name_stem}{file_type}.transcribed.txt"
    print(f"Created {output_file} using CLI")
    cmd_list = ["whisper", file, "--model", modelType, "--language", language]
    print(f"attempting command: {' '.join(cmd_list)}")
    with open(output_file, "w", encoding="utf-8") as f:
        ret = subprocess.run(cmd_list, stdout=f, check=True)
    return ret


def get_files_recursive(directory, pattern=None, ignore=None, action=None):
    """Return a list of files matching a pattern in a directory recursively"""

    if pattern is None:
        pattern = re.compile(r".*\.(wav|mp3|mp4|avi|mov|flv|mkv|wmv)$")
    files = [
        str(p) for p in pathlib.Path(directory).rglob("*") if pattern.match(str(p))
    ]
    if ignore is not None:
        files = [f for f in files if not ignore in f]
    if action is not None:
        files = [action(f) for f in files]
    return files


def transcribe_file(file, modelType="large", force=True, climode=True):
    """Transcribe a file and return the result"""

    print("Attempting {}".format(file))
    transcribed_file = f"{file}.transcribed.txt"
    # if the file has already been transcribed, skip it

    if pathlib.Path(transcribed_file).exists() and not force:
        print("Skipping {}".format(file))
        return transcribed_file
    else:
        if force:
            print("Forcing transcription of {}".format(file))
        if climode:
            print(f"Transcribing {file} using CLI")
            start = time.time()
            tfile_cli = transcribe_file_cli(file, modelType)
            duration = f"{time.time() - start:.2f}"
            print(
                f"Transcribed Complete for {transcribed_file} with duration: {duration}"
            )
            return tfile_cli
        try:
            print("Confirmed Transcribing {}".format(file))
            model = whisper.load_model(modelType)
            start = time.time()
            result = model.transcribe(file)
            # Dump the result to a file
            with open(transcribed_file, "w", encoding="utf-8") as f:
                f.write(result["text"])
            duration = f"{time.time() - start:.2f}"
            print(
                f"Transcribed Complete for {transcribed_file} with duration: {duration}"
            )
            # Write the entire transcription as a json file
            with open(f"{transcribed_file}.json", "w", encoding="utf-8") as jf:
                jf.write(result)
            return transcribed_file
        except RuntimeError as e:
            print("Error: {}".format(e))
            print("Error transcribing {}".format(file))
            return file


# click group
@click.group()
def cli():
    """Transcribe and summarize a directory of audio or video files"""


@cli.command("cpu-count")
def cpucount():
    """Return the number of CPUs"""

    print(f"CPU Count: {multiprocessing.cpu_count()}")


@cli.command("transcribe")
@click.option("--directory", default=".", help="Directory to transcribe")
@click.option("--pattern", default=None)
@click.option("--ignore", default=".cmproj", help="Pattern to ignore files")
@click.option("--model", default="base.en", help="Model to use")
@click.option("--force", is_flag=True, help="Force transcribe")
@click.option("--climode", is_flag=True, help="Use CLI mode")
def transcribe(
    directory,
    pattern,
    ignore,
    model,
    force,
    climode,
):
    """ "Transcribes a directory of audio or video files"""

    # import ipdb; ipdb.set_trace()
    files = get_files_recursive(directory, pattern, ignore)
    for f in files:
        transcribe_file(f, modelType=model, force=force, climode=climode)


@cli.command("discover")
@click.option("--directory", default=".", help="Directory to search for files")
@click.option("--pattern", default=None, help="Pattern to match files")
@click.option("--ignore", default=".cmproj", help="Pattern to ignore files")
def discover(
    directory,
    pattern,
    ignore,
):
    """Discover files in a directory matching a pattern"""

    # import ipdb; ipdb.set_trace()
    files = get_files_recursive(directory, pattern, ignore)
    for f in files:
        print(f)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
