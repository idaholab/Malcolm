#!/bin/sh

NON_USB_DEVICES="$(
  find /sys/block -mindepth 1 -maxdepth 1 -type l \( -name '[hs]d*' -o -name 'nvme*' \) -exec ls -l '{}' ';' |
    grep -v "usb" |
    sed 's@^.*\([hs]d[a-z]\+\|nvme[0-9]\+\).*$@/dev/\1@' |
    sed -e :a -e '$!N; s/\n/|/; ta'
)"

if [ -z "$NON_USB_DEVICES" ]; then
  echo "No non-USB installation target found; refusing to select installer media" >&2
  echo "/dev/__malcolm_no_install_target__"
  exit 1
fi

parted_devices |
  egrep "^(${NON_USB_DEVICES})" |
  sort -k2n |
  head -1 |
  cut -f1
