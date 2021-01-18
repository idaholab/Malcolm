##! Zeek local site policy. Customize as appropriate.
##!
##! See https://github.com/zeek/zeekctl
##!     https://docs.zeek.org/en/stable/script-reference/scripts.html
##!     https://github.com/zeek/zeek/blob/master/scripts/site/local.zeek

global disable_bzar = (getenv("ZEEK_DISABLE_MITRE_BZAR") == "") ? F : T;
global disable_hash_all_files = (getenv("ZEEK_DISABLE_HASH_ALL_FILES") == "") ? F : T;
global disable_log_passwords = (getenv("ZEEK_DISABLE_LOG_PASSWORDS") == "") ? F : T;
global disable_mqtt = (getenv("ZEEK_DISABLE_MQTT") == "") ? F : T;
global disable_pe_xor = (getenv("ZEEK_DISABLE_PE_XOR") == "") ? F : T;
global disable_quic = (getenv("ZEEK_DISABLE_QUIC") == "") ? F : T;
global disable_ssl_validate_certs = (getenv("ZEEK_DISABLE_SSL_VALIDATE_CERTS") == "") ? F : T;
global disable_telnet = (getenv("ZEEK_DISABLE_TELNET") == "") ? F : T;
global disable_track_all_assets = (getenv("ZEEK_DISABLE_TRACK_ALL_ASSETS") == "") ? F : T;
global disable_wireguard = (getenv("ZEEK_DISABLE_WIREGUARD") == "") ? F : T;
global disable_wireguard_transport_packets = (getenv("ZEEK_DISABLE_WIREGUARD_TRANSPORT_PACKETS") == "") ? F : T;

redef Broker::default_listen_address = "127.0.0.1";
redef ignore_checksums = T;

@if (!disable_log_passwords)
  redef HTTP::default_capture_password = T;
  redef FTP::default_capture_password = T;
  redef SOCKS::default_capture_password = T;
@endif

@load tuning/defaults
@load misc/scan
@load frameworks/software/vulnerable
@load frameworks/software/version-changes
@load frameworks/software/windows-version-detection
@load-sigs frameworks/signatures/detect-windows-shells
@load protocols/conn/known-hosts
@load protocols/conn/known-services
@load protocols/dhcp/software
@load protocols/dns/detect-external-names
@load protocols/ftp/detect
@load protocols/ftp/detect-bruteforcing.zeek
@load protocols/ftp/software
@load protocols/http/detect-sqli
@load protocols/http/detect-webapps
@load protocols/http/software
@load protocols/http/software-browser-plugins
@load protocols/mysql/software
@load protocols/ssl/weak-keys
@load protocols/smb/log-cmds
@load protocols/smtp/software
@load protocols/ssh/detect-bruteforcing
@load protocols/ssh/geo-data
@load protocols/ssh/interesting-hostnames
@load protocols/ssh/software
@load protocols/ssl/known-certs
@load protocols/ssl/log-hostcerts-only
@if (!disable_ssl_validate_certs)
  @load protocols/ssl/validate-certs
@endif
@if (!disable_track_all_assets)
  @load tuning/track-all-assets.zeek
@endif
@if (!disable_hash_all_files)
  @load frameworks/files/hash-all-files
@endif
@load policy/protocols/conn/vlan-logging
@load policy/protocols/conn/mac-logging
@load policy/protocols/modbus/known-masters-slaves
@if (!disable_mqtt)
  @load policy/protocols/mqtt
@endif

# @load frameworks/files/detect-MHR

# custom packages installed manually

@if (!disable_telnet)
  @load ./login.zeek
@endif

@if (!disable_wireguard)
  @load ./spicy-noise
  event zeek_init() &priority=-5 {
    if (disable_wireguard_transport_packets) {
      Log::remove_default_filter(WireGuard::WGLOG);
      Log::add_filter(WireGuard::WGLOG,
        [$name = "wireguard-verbose",
         $pred(rec: WireGuard::Info) = { return (rec$msg_type != "TRANSPORT"); }]);
    }
  }
@endif

@if (!disable_pe_xor)
  @load Corelight/PE_XOR
@endif

@if (!disable_quic)
  @load Salesforce/GQUIC
@endif

@if (!disable_bzar)
  @load ./bzar
@endif

# custom packages managed by zkg via packages/packages.zeek
@load ./packages/packages.zeek

# and apparently some installed packages (BRO::LDAP) are loaded automatically
#

# these redefs need to happen after the packages are loaded
@if (!disable_log_passwords)
  redef SNIFFPASS::log_password_plaintext = T;
@endif
redef SNIFFPASS::notice_log_enable = F;
