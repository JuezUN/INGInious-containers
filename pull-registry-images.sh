#!/usr/bin/env bash
set -e

tag="latest";

while getopts ":t:" opt; do
  case $opt in
    t)
      echo "tag flag was triggered, Tag: $OPTARG" >&2;
      tag="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done
read -p "Are you sure to pull grading images with tag :"$tag" ? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
        echo "-------------------------------------------------------"
        echo "- Pulling grading images with tag :"$tag""
        echo "-------------------------------------------------------"
        docker pull unjudge/inginious-c-base:"$tag"
        docker pull unjudge/inginious-c-default:"$tag"
        docker pull unjudge/uncode-c-base:"$tag"
        docker pull unjudge/inginious-c-multilang:"$tag"
        docker pull unjudge/inginious-c-datascience:"$tag"
        docker pull unjudge/hdl-uncode:"$tag"
        docker pull unjudge/inginious-c-notebook:"$tag"
        echo "-------------------------------------------------------"
        echo "- Tagging grading images to (ingi/inginious-c)"
        echo "-------------------------------------------------------"
        docker tag unjudge/inginious-c-base:"$tag" ingi/inginious-c-base
        docker tag unjudge/inginious-c-default:"$tag" ingi/inginious-c-default
        docker tag unjudge/inginious-c-multilang:"$tag" ingi/inginious-c-multilang
        docker tag unjudge/inginious-c-datascience:"$tag" ingi/inginious-c-datascience
        docker tag unjudge/hdl-uncode:"$tag" ingi/hdl-uncode
        docker tag unjudge/inginious-c-notebook:"$tag" ingi/inginious-c-notebook
fi