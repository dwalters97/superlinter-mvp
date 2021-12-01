#!/bin/zsh

FILEPATH="$PWD"
COMMAND_OPTION=""

for i in "$@"; do
  case $i in
    -cmd=*|--command-option=*)
      COMMAND_OPTION="${i#*=}"
      shift # past argument=value
      ;;
    -p=*|--path=*)
      FILEPATH="${i#*=}"
      shift # past argument=value
      ;;
    *)
      # unknown option
      ;;
  esac
done

eval "docker run -e RUN_LOCAL=true -e COMMAND_OPTION='$COMMAND_OPTION' -v $FILEPATH:/tmp/lint dev-superlinter"