#!/bin/bash -e

SCRIPT_NAME=`basename "$0"`

# Default values
DAYS=5
FOLDER=/tmp
FORCE=false
PREFIX=logs_

help()
{
   # Display Help
   echo "Copy docker container or service logs to S3."
   echo
   echo "Syntax: $SCRIPT_NAME [--service docker_swarm_service|--container docker_container|--days|V]"
   echo "options:"
   echo "--service   docker_swarm_service  Copy the logs of the docker swarm service."
   echo "--container docker_container      Copy the logs of the docker container"
   echo "--days      5                     The number of days of logs should be copied."
   echo "--folder    /tmp                  The temporary folder that should be used to store the temporary files."
   echo "--force                           Do not check the first logging message timestamp."
   echo "--test                            Run it on test mode, it won't send nothing to S3."
   echo "--target    's3://bucket/folder/' The S3 folder were the log file should be stored."
   echo "--verbose                         Print all the commands."
   echo
}

###########################
# Parse parameters
###########################
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      help
      exit
      ;;
    --service)
      SERVICE="$2"
      shift # past argument
      shift # past value
      ;;
    --container)
      CONTAINER="$2"
      shift # past argument
      shift # past value
      ;;
    --days)
      DAYS="$2"
      shift # past argument
      shift # past value
      ;;
    --folder)
      FOLDER="$2"
      shift # past argument
      shift # past value
      ;;
    --force)
      FORCE=true
      shift # past argument
      ;;
    --test)
      noop="echo Would have run: "
      shift # past argument
      ;;
    --target)
      TARGET="$2"
      shift # past argument
      shift # past value
      ;;
    --verbose)
      VERBOSE=true
      shift # past argument
      ;;
    # -*|--*)
    #   echo "Unknown option $1"
    #   exit 1
    #   ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done
set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

# the rest of the parameters as passed directly to s3cmd
S3CMD_PARAMETERS=$*

# end of parse parameters

# Print commands in test mode
if [ "${VERBOSE}" == "true" ];
then
  set -x
fi

# Check service variable
if [ -z "${SERVICE}" ] && [ -z "$CONTAINER" ];
then
  echo "Service or container are required. Add one of the parameters like: `--service openedx_nginx` or `--container nau-balancer`";
  exit -1;
fi

# Check service variable
if [ -z "${SERVICE}" ];
then
  SERVICE_CONTAINER=$CONTAINER
else
  SERVICE_CONTAINER=$SERVICE
  DOCKER_ARG=service
fi

# Check target variable
if [ -z ${TARGET} ];
then
    echo "Target is required. Add parameter like: --target s3://my-bucket/folder_to_save_logs/ ";
    exit -1;
fi

ALL_LOGS_FILE=/tmp/$PREFIX$SERVICE_CONTAINER; \
HOURS_FROM_DOCKER_SERVICE_LOGS="$((($DAYS+1)*24))"

# Print the next message if in verbose mode
if [ -z ${VERBOSE} ];
then
  echo "Sending logs of the docker service/container: '$SERVICE_CONTAINER'"
  echo "From the last '$DAYS' days"
  echo "Using temporary folder: '$FOLDER'"
  echo "Target S3 folder '$TARGET'"
  echo "Hours from containers '$HOURS_FROM_DOCKER_SERVICE_LOGS'"
fi

# get all logs to a file
# timeout is an hack because the docker logs sometimes didn't stop
timeout 5m docker $DOCKER_ARG logs --timestamps --since ${HOURS_FROM_DOCKER_SERVICE_LOGS}h $SERVICE_CONTAINER 2>&1 > $ALL_LOGS_FILE || echo;

FIRST_DAY_OF_LOGS_ISO=$(docker $DOCKER_ARG logs --timestamps $SERVICE_CONTAINER 2>&1 | head -1 | egrep -o '^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
FIRST_DAY_OF_LOGS_DATE=$(date -d $FIRST_DAY_OF_LOGS_ISO)

if [ -z ${VERBOSE} ];
then
  echo "First day of logs: '$FIRST_DAY_OF_LOGS_DATE'"
fi

# for each day
for i in $(seq 1 $DAYS); do
    DAY_ISO=$(date --iso-8601 --date="-${i} day");
    DAY=$(date '+%Y%m%d' --date="-${i} day");

    if [ "$FORCE" = "true" ] && [ $(date --date="-${i} day") -g $FIRST_DAY_OF_LOGS_DATE ];
    then
        echo "Stopping because we only have partial logs for the $DAY_ISO"
        exit -1;
    fi

    echo "Sending logs of $DAY_ISO";
    FILE_FOR_DAY=$FOLDER/${PREFIX}${SERVICE_CONTAINER}_${DAY};
    awk "/${DAY_ISO}/ {print}" $ALL_LOGS_FILE > $FILE_FOR_DAY;

    gzip $FILE_FOR_DAY

    $noop s3cmd $S3CMD_PARAMETERS --multipart-chunk-size-mb 5120 --disable-multipart sync $FILE_FOR_DAY.gz "$TARGET";

done

# clean files
rm -f $FOLDER/logs_*
