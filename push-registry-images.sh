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


read -p "Are you sure to push main container images with tag:"$tag" ? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: inginious-c-base:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/inginious-c-base:"$tag"
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: inginious-c-default:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/inginious-c-default:"$tag"
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: uncode-c-base:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/uncode-c-base:"$tag"
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: inginious-c-multilang:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/inginious-c-multilang:"$tag"
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: inginious-c-datascience:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/inginious-c-datascience:"$tag"
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: hdl-uncode:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/hdl-uncode:"$tag"
    echo "-------------------------------------------------------"
    echo "- Pushing registry image: inginious-c-notebook:"$tag""
    echo "-------------------------------------------------------"
    docker push unjudge/inginious-c-notebook:"$tag"
fi