#!/bin/sh
# lab1 统一验收入口
# 用法: sh tools/lab1-autograder/run.sh <学生代码树路径> <学号>
set -e
DIR=$(dirname "$0")
exec python3 "$DIR/autograde.py" --tree "$1" --sid "$2"
