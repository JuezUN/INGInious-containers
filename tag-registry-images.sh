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
read -p "Are you sure to tag grading images (ingi/ingi-c) with tag :"$tag" ? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
        echo "-------------------------------------------------------"
        echo "- Tagging grading images with tag: "$tag" "
        echo "-------------------------------------------------------"
        docker tag ingi/inginious-c-base unjudge/inginious-c-base:"$tag"
        docker tag ingi/inginious-c-default unjudge/inginious-c-default:"$tag"
        docker tag unjudge/uncode-c-base unjudge/uncode-c-base:"$tag"
        docker tag ingi/inginious-c-multilang unjudge/inginious-c-multilang:"$tag"
        docker tag ingi/inginious-c-datascience unjudge/inginious-c-datascience:"$tag"
        docker tag ingi/hdl-uncode unjudge/hdl-uncode:"$tag"
        docker tag ingi/inginious-c-notebook unjudge/inginious-c-notebook:"$tag"
fi