#!/usr/bin/env bash
set -e

grading=("datascience" "notebook" "multilang")

for container in "${grading[@]}"; do
        echo "-------------------------------------------------------"
        echo "- Destroying grading image: " "$container"
        echo "-------------------------------------------------------"
        docker rmi -f ingi/inginious-c-"$container"
done

echo "-------------------------------------------------------"
echo "- Destroying grading image: hdl"
echo "-------------------------------------------------------"
docker rmi -f ingi/hdl-uncode
echo "-------------------------------------------------------"
echo "- Destroying grading image: uncode-c-base"
echo "-------------------------------------------------------"
docker rmi -f unjudge/uncode-c-base


echo "-------------------------------------------------------"
echo "- Building grading image: uncode-c-base"
echo "-------------------------------------------------------"
docker build -t "unjudge/uncode-c-base" "grading/uncode"

echo "-------------------------------------------------------"
echo "- Building grading image: hdl"
echo "-------------------------------------------------------"
docker build -t "ingi/hdl-uncode" "grading/hdl"

echo "-------------------------------------------------------"
echo "- Building grading image: multilang"
echo "-------------------------------------------------------"
docker build -t "ingi/inginious-c-multilang" -t "unjudge/inginious-c-multilang" "grading/multilang"

echo "-------------------------------------------------------"
echo "- Building grading image: notebook"
echo "-------------------------------------------------------"
docker build -t "ingi/inginious-c-notebook" "grading/notebook"


echo "-------------------------------------------------------"
echo "- Building grading image: data_science"
echo "-------------------------------------------------------"
docker build -t "ingi/inginious-c-datascience" "grading/data_science"
echo "-------------------------------------------------------"
echo "- Destroying grading image unjudge/inginious-c-multilang used to build data_science"
echo "-------------------------------------------------------"
docker rmi -f unjudge/inginious-c-multilang