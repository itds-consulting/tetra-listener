#!/bin/bash
# inotify watches an directory with demodulated recordings and play them via mplayer
# while using minimum resources when not needed (thats why it is using inotify)

DIRECTORY_TO_WATCH="${HOME}/tetra-rec"
FIFO_MPLAYER_QUEUE="${HOME}/.mplayer/pipe"
FIFO_MKFIFO_OPTIONS="-m 600"
MPLAYER_SPEEDUP_RATE="1"
# audio files can be played faster by speedup rate defined above
# '-ac tremor,' is an attempt to prefer low cpu OGG decoder (note that comma is fine (see MPLAYER docs))
MPLAYER_OPTIONS="-vo null -ac tremor, -speed ${MPLAYER_SPEEDUP_RATE} -af scaletempo=scale=${MPLAYER_SPEEDUP_RATE}"

while getopts ":f:" opt; do
  case ${opt} in
    f)
      # this primary solves situation when named piped file was deleted and last audio file
      # would be skipped due to this. this script detects such situation,restarts itself
      # and play last audio file submitted as a parameter to -f first
      PLAY_FIRST="${OPTARG}"
      ;;
    \?)
      echo "** Invalid option: -${OPTARG}" >&2
      exit 1
      ;;
    :)
      echo "** Option -${OPTARG} requires an argument." >&2
      exit 2
      ;;
  esac
done

# cleanup if Ctrl+C is used to end this script
trap ctrl_c INT
function ctrl_c() {
        echo "** Trapped [CTRL-C]"
        kill -9 "${MPLAYER_PID}"
        rm -f "${FIFO_MPLAYER_QUEUE}" 
}

# if named pipe file disappears script is restarted with -f last.ogg submitted (so its not skipped)
function restart() {
        echo -e "!! I will now try to restart this script..."
        rm -f "${FIFO_MPLAYER_QUEUE}"
        ME="$(readlink -e ${0})"
        kill -9 "${MPLAYER_PID}"
        ${ME} -f "${path}/${file}"
}

function submit_to_mplayer() {
        echo "loadfile ${1} 1" > ${FIFO_MPLAYER_QUEUE}
}

# ask for deletion of orphaned named pipe file from previous run
if [[ -e ${FIFO_MPLAYER_QUEUE} ]]; then
    read -p "File ${FIFO_MPLAYER_QUEUE} exists. Do you want to delete? [y/n] " delete
    if [[ $delete == [yY] ]]; then  ## Only delete if y/Y is pressed. Any other key would cancel it.
        rm -f "${FIFO_MPLAYER_QUEUE}" && echo "File deleted."
    fi
fi

# named pipe file is created to send newly demodulated files to mplayer queue
mkfifo ${FIFO_MKFIFO_OPTIONS} "${FIFO_MPLAYER_QUEUE}" && echo "** named pipe ${FIFO_MPLAYER_QUEUE} created"


# mplayer slave process will start, ready to play files submited to named pipe (queue)
mplayer -slave -idle -input file="${FIFO_MPLAYER_QUEUE}" ${MPLAYER_OPTIONS} &
[ $? -eq 0 ] && echo "** mplayer slave process started and waiting for audio files"
MPLAYER_PID="$(jobs -p -l|awk '/[0-9]/ {print $2}')"
echo "** mplayer slave is running as PID ${MPLAYER_PID}"

[ -n "${PLAY_FIRST}" ] && echo "** ${PLAY_FIRST} from previous run will be played first" >&2 && submit_to_mplayer "${PLAY_FIRST}"


# we are starting to submit newly created files from directory watched to the mplayer slave process
# to be played one after another
echo -e "\n** Supervising an ${DIRECTORY_TO_WATCH} directory..."
echo -e "\n** Hit [CTRL+C] to stop everything."

# most important cycle here is waiting for an inotify event implying new audio file was written
# and submits such audio file to mplayer queue
inotifywait -m "${DIRECTORY_TO_WATCH}" -r -e CLOSE_WRITE |
    while read path action file; do
        echo -e "** The file [${path}/${file}] appeared via ${action} event.\n** Submiting to mplayer queue..."
        # echo "loadfile ${path}/${file} 1" > ${FIFO_MPLAYER_QUEUE}
        submit_to_mplayer "${path}/${file}"
        [ ! -p ${FIFO_MPLAYER_QUEUE} ] && echo -e "\n!! BEWARE !!! ${FIFO_MPLAYER_QUEUE} is NOT a named pipe file (was probably deleted).\n!! RESTART script. Otherwise will probably not work as expected!" && restart 
    done

