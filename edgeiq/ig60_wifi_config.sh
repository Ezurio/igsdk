#!/bin/bash
# Copyright (c) 2024 Ezurio LLC.
#
# IG60 helper script for remotely configuring Wi-Fi connections via EdgeIQ. This
# script is essentially a wrapper around NetworkManager's command line tool (nmcli)
# and can be used either as is, or as a template for a customized, bespoke solution.
#
# Usage: ig60_wifi_config.sh -s/--ssid <SSID> [OPTIONS]
#
#   -s, --ssid                    SSID of the Wi-Fi network. Must be specified.
#
# OPTIONS
#   *** WPA ***
#   --psk                         Pre-Shared-Key for WPA networks. For WPA-PSK,
#                                 it's either an ASCII passphrase of 8 to 63
#                                 characters that is (as specified in the 802.11i
#                                 standard) hashed to derive the actual key, or
#                                 the key in form of 64 hexadecimal character.
#                                 The WPA3-Personal networks use a passphrase of
#                                 any length for SAE authentication.
#                                 (802-11-wireless-security.psk)
#
#   *** Enterprise (802.1x) ***
#   --anonymous-identity          Anonymous identity string for EAP authentication
#                                 methods. Used as the unencrypted identity with
#                                 EAP types that support different tunneled
#                                 identity like EAP-TTLS.
#                                 (802-1x.anonymous-identity)
#   --auth-retries                The number of retries for the authentication.
#                                 Zero means to try indefinitely; -1 means to use
#                                 a global default. If the global default is not
#                                 set, the authentication retries for 3 times
#                                 before failing the connection.
#                                 (connection.auth-retries)
#   --ca-cert                     Contains the CA certificate if used by the EAP
#                                 method specified in the "eap" property.
#                                 (802-1x.ca-cert)
#   --ca-cert-password            The password used to access the CA certificate
#                                 stored in "ca-cert" property. Only makes sense
#                                 if the certificate is stored on a PKCS#11 token
#                                 that requires a login. (802-1x.ca-cert-password)
#   --client-cert                 Contains the client certificate if used by the
#                                 EAP method specified in the "eap" property.
#                                 (802-1x.client-cert)
#   --client-cert-password        The password used to access the client
#                                 certificate stored in "client-cert" property.
#                                 Only makes sense if the certificate is stored on
#                                 a PKCS#11 token that requires a login.
#                                 (802-1x.client-cert-password)
#   --eap                         The allowed EAP method to be used when
#                                 authenticating to the network with 802.1x. Valid
#                                 methods are: "leap", "md5", "tls", "peap",
#                                 "ttls", "pwd", and "fast". Each method requires
#                                 different configuration using the properties of
#                                 this setting; refer to wpa_supplicant
#                                 documentation for the allowed combinations.
#                                 (802-1x.eap)
#   --identity                    Identity string for EAP authentication methods.
#                                 Often the user's user or login name.
#                                 (802-1x.identity)
#   --pac-file                    UTF-8 encoded file path containing PAC for
#                                 EAP-FAST. (802-1x.pac-file)
#   --pac-file-password           The password used to decrypt the PAC file
#                                 specified in the \"pac-file\" property.
#                                 (802-1x.pac-file-password)
#   --password                    UTF-8 encoded password used for EAP
#                                 authentication methods. (802-1x.password)
#   --phase1-fast-provisioning    Enables or disables in-line provisioning of
#                                 EAP-FAST credentials when FAST is specified as
#                                 the EAP method in the "eap" property. Recognized
#                                 values are "0" (disabled), "1" (allow
#                                 unauthenticated provisioning), "2" (allow
#                                 authenticated provisioning), and "3" (allow both
#                                 authenticated and unauthenticated provisioning).
#                                 See the wpa_supplicant documentation for more
#                                 details. (802-1x.phase1-fast-provisioning)
#   --phase2-auth                 Specifies the allowed "phase 2" inner
#                                 authentication method when an EAP method that
#                                 uses an inner TLS tunnel is specified in the
#                                 "eap" property. For TTLS this property selects
#                                 one of the supported non-EAP inner methods:
#                                 "pap", "chap", "mschap", "mschapv2" while
#                                 "phase2-autheap" selects an EAP inner method.
#                                 For PEAP this selects an inner EAP method, one
#                                 of: "gtc", "otp", "md5" and "tls". Each
#                                 "phase 2" inner method requires specific
#                                 parameters for successful authentication; see
#                                 the wpa_supplicant documentation for more
#                                 details. Both "phase2-auth" and "phase2-autheap"
#                                 cannot be specified. (802-1x.phase2-auth)
#   --phase2-autheap              Specifies the allowed "phase 2" inner EAP-based
#                                 authentication method when TTLS is specified in
#                                 the "eap" property. Recognized EAP-based
#                                 "phase 2" methods are "md5", "mschapv2", "otp",
#                                 "gtc", and "tls". Each "phase 2" inner method
#                                 requires specific parameters for successful
#                                 authentication; see the wpa_supplicant
#                                 documentation for more details.
#                                 (802-1x.phase2-autheap)
#   --phase2-ca-cert              Contains the "phase 2" CA certificate if used by
#                                 the EAP method specified in the "phase2-auth" or
#                                 "phase2-autheap" properties.
#                                 (802-1x.phase2-ca-cert)
#   --phase2-ca-cert-password     The password used to access the "phase2" CA
#                                 certificate stored in "phase2-ca-cert" property.
#                                 Only makes sense if the certificate is stored on
#                                 a PKCS#11 token that requires a login.
#                                 (802-1x.phase2-ca-cert-password)
#   --phase2-client-cert          Contains the "phase 2" client certificate if
#                                 used by the EAP method specified in the
#                                 "phase2-auth" or "phase2-autheap" properties.
#                                 (802-1x.phase2-client-cert)
#   --phase2-client-cert-password The password used to access the "phase2" client
#                                 certificate stored in "phase2-client-cert"
#                                 property. Only makes sense if the certificate is
#                                 stored on a PKCS#11 token that requires a login.
#                                 (802-1x.phase2-client-cert-password)
#   --phase2-private-key          Contains the "phase 2" inner private key when
#                                 the "phase2-auth" or "phase2-autheap" property
#                                 is set to "tls".
#                                 (802-1x.phase2-private-key)
#   --phase2-private-key-password The password used to decrypt the "phase 2"
#                                 private key specified in the
#                                 "phase2-private-key" property when the private
#                                 key either uses the path scheme, or is a PKCS#12
#                                 format key. (802-1x.phase2-private-key-password)
#   --private-key                 Contains the private key when the "eap" property
#                                 is set to "tls". WARNING: "private-key" is not a
#                                 "secret" property, and thus unencrypted private
#                                 key data using the BLOB scheme may be readable
#                                 by unprivileged users. Private keys should
#                                 always be encrypted with a private key password
#                                 to prevent unauthorized access to unencrypted
#                                 private key data. (802-1x.private-key)
#   --private-key-password        The password used to decrypt the private key
#                                 specified in the "private-key" property when the
#                                 private key either uses the path scheme, or if
#                                 the private key is a PKCS#12 format key.
#                                 (802-1x.private-key-password)
#   --proactive-key-caching       Boolean to enable Proactive Key Caching, also
#                                 known as Opportunistic Key Caching (OKC).
#                                 (802-11-wireless-security.proactive-key-caching)
#
#   *** WEP ***
#   --wep-key                     A string containing the WEP key; can be either 5
#                                 or 13 hexadecimal bytes (10 or 26 hex chars) or
#                                 an ASCII string of 5 to 13 characters. WEP key
#                                 is assumed to be index 0.
#                                 (802-11-wireless-security.wep-key0)
#
#   *** Miscellaneous ***
#   -a, --activate                Indicates to automatically activate the
#                                 connection. Optional.
#   --autoconnect-retries         The number of times a connection should be tried
#                                 when autoactivating before giving up. Zero means
#                                 forever, -1 means the global default (4 times if
#                                 not overridden). Setting this to 1 means to try
#                                 activation only once before blocking
#                                 autoconnect. Note that after a timeout,
#                                 NetworkManager will try to autoconnect again.
#                                 (connection.autoconnect-retries)
#   --bgscan                      Configures scanning/roaming options
#                                 (802-11-wireless.bgscan)
#   -d, --disable-ipv6            Indicates IPv6 should be disabled on the
#                                 connection. Optional.
#   -h, --hidden                  If TRUE, indicates that the network is a
#                                 non-broadcasting network that hides its SSID.
#                                 (802-11-wireless.hidden)
#   -o, --open                    Boolean specifying whether or not the AP is an
#                                 "open" network (i.e., no security is used).
#   --pairwise                    A list of pairwise encryption algorithms which
#                                 prevents connections to Wi-Fi networks that do
#                                 not utilize one of the algorithms in the list.
#                                 For maximum compatibility leave this property
#                                 empty. Each list element may be one of "tkip" or
#                                 "ccmp". (802-11-wireless-security.pairwise)
#   -p, --priority                A number indicating the priority of the
#                                 connection. A connection can be removed by
#                                 specifying a priority of '-1'. Optional,
#                                 default is 0.
#   --proto                       List of strings specifying the allowed WPA
#                                 protocol versions to use. Each element may be
#                                 one "wpa" (allow WPA) or "rsn" (allow WPA2/RSN).
#                                 If not specified, both WPA and RSN connections
#                                 are allowed. (802-11-wireless-security.proto)
#
# Check here for more information on the many configuration settings supported by
# NetworkManager's command line tool (nmcli):
# https://man.archlinux.org/man/nmcli.1
#

# Make verbose log, fail on uncaught errors
set -xe

NM_SYSTEM_CONNECTIONS_DIR=/data/secret/system-connections
NMCLI=/bin/nmcli
WIFI_INTERFACE_NAME="wlan0"

programname=$(basename $0)

#
# Helper function to print an error message and exit with a failure code
#
cleanup_and_fail(){
    echo $1
    exit 1
}

#
# Helper function to print out the script usage
#
show_usage() {
    echo -e "Usage: $programname -s/--ssid <SSID> [OPTIONS]\n\
\n\
  -s, --ssid                    SSID of the Wi-Fi network. Must be specified.\n\
\n\
OPTIONS\n\
  *** WPA ***\n\
  --psk                         Pre-Shared-Key for WPA networks. For WPA-PSK,\n\
                                it's either an ASCII passphrase of 8 to 63\n\
                                characters that is (as specified in the 802.11i\n\
                                standard) hashed to derive the actual key, or\n\
                                the key in form of 64 hexadecimal character.\n\
                                The WPA3-Personal networks use a passphrase of\n\
                                any length for SAE authentication.\n\
                                (802-11-wireless-security.psk)\n\
\n\
  *** Enterprise (802.1x) ***\n\
  --anonymous-identity          Anonymous identity string for EAP authentication\n\
                                methods. Used as the unencrypted identity with\n\
                                EAP types that support different tunneled\n\
                                identity like EAP-TTLS.\n\
                                (802-1x.anonymous-identity)\n\
  --auth-retries                The number of retries for the authentication.\n\
                                Zero means to try indefinitely; -1 means to use\n\
                                a global default. If the global default is not\n\
                                set, the authentication retries for 3 times\n\
                                before failing the connection.\n\
                                (connection.auth-retries)\n\
  --ca-cert                     Contains the CA certificate if used by the EAP\n\
                                method specified in the \"eap\" property.\n\
                                (802-1x.ca-cert)\n\
  --ca-cert-password            The password used to access the CA certificate\n\
                                stored in \"ca-cert\" property. Only makes sense\n\
                                if the certificate is stored on a PKCS#11 token\n\
                                that requires a login. (802-1x.ca-cert-password)\n\
  --client-cert                 Contains the client certificate if used by the\n\
                                EAP method specified in the \"eap\" property.\n\
                                (802-1x.client-cert)\n\
  --client-cert-password        The password used to access the client\n\
                                certificate stored in \"client-cert\" property.\n\
                                Only makes sense if the certificate is stored on\n\
                                a PKCS#11 token that requires a login.\n\
                                (802-1x.client-cert-password)\n\
  --eap                         The allowed EAP method to be used when\n\
                                authenticating to the network with 802.1x. Valid\n\
                                methods are: \"leap\", \"md5\", \"tls\", \"peap\",\n\
                                \"ttls\", \"pwd\", and \"fast\". Each method requires\n\
                                different configuration using the properties of\n\
                                this setting; refer to wpa_supplicant\n\
                                documentation for the allowed combinations.\n\
                                (802-1x.eap)\n\
  --identity                    Identity string for EAP authentication methods.\n\
                                Often the user's user or login name.\n\
                                (802-1x.identity)\n\
  --pac-file                    UTF-8 encoded file path containing PAC for\n\
                                EAP-FAST. (802-1x.pac-file)\n\
  --pac-file-password           The password used to decrypt the PAC file\n\
                                specified in the \"pac-file\" property.\n\
                                (802-1x.pac-file-password)\n\
  --password                    UTF-8 encoded password used for EAP\n\
                                authentication methods. (802-1x.password)\n\
  --phase1-fast-provisioning    Enables or disables in-line provisioning of\n\
                                EAP-FAST credentials when FAST is specified as\n\
                                the EAP method in the \"eap\" property. Recognized\n\
                                values are \"0\" (disabled), \"1\" (allow\n\
                                unauthenticated provisioning), \"2\" (allow\n\
                                authenticated provisioning), and \"3\" (allow both\n\
                                authenticated and unauthenticated provisioning).\n\
                                See the wpa_supplicant documentation for more\n\
                                details. (802-1x.phase1-fast-provisioning)\n\
  --phase2-auth                 Specifies the allowed \"phase 2\" inner\n\
                                authentication method when an EAP method that\n\
                                uses an inner TLS tunnel is specified in the\n\
                                \"eap\" property. For TTLS this property selects\n\
                                one of the supported non-EAP inner methods:\n\
                                \"pap\", \"chap\", \"mschap\", \"mschapv2\" while\n\
                                \"phase2-autheap\" selects an EAP inner method.\n\
                                For PEAP this selects an inner EAP method, one\n\
                                of: \"gtc\", \"otp\", \"md5\" and \"tls\". Each\n\
                                \"phase 2\" inner method requires specific\n\
                                parameters for successful authentication; see\n\
                                the wpa_supplicant documentation for more\n\
                                details. Both \"phase2-auth\" and \"phase2-autheap\"\n\
                                cannot be specified. (802-1x.phase2-auth)\n\
  --phase2-autheap              Specifies the allowed \"phase 2\" inner EAP-based\n\
                                authentication method when TTLS is specified in\n\
                                the \"eap\" property. Recognized EAP-based\n\
                                \"phase 2\" methods are \"md5\", \"mschapv2\", \"otp\",\n\
                                \"gtc\", and \"tls\". Each \"phase 2\" inner method\n\
                                requires specific parameters for successful\n\
                                authentication; see the wpa_supplicant\n\
                                documentation for more details.\n\
                                (802-1x.phase2-autheap)\n\
  --phase2-ca-cert              Contains the \"phase 2\" CA certificate if used by\n\
                                the EAP method specified in the \"phase2-auth\" or\n\
                                \"phase2-autheap\" properties.\n\
                                (802-1x.phase2-ca-cert)\n\
  --phase2-ca-cert-password     The password used to access the \"phase2\" CA\n\
                                certificate stored in \"phase2-ca-cert\" property.\n\
                                Only makes sense if the certificate is stored on\n\
                                a PKCS#11 token that requires a login.\n\
                                (802-1x.phase2-ca-cert-password)\n\
  --phase2-client-cert          Contains the \"phase 2\" client certificate if\n\
                                used by the EAP method specified in the\n\
                                \"phase2-auth\" or \"phase2-autheap\" properties.\n\
                                (802-1x.phase2-client-cert)\n\
  --phase2-client-cert-password The password used to access the \"phase2\" client\n\
                                certificate stored in \"phase2-client-cert\"\n\
                                property. Only makes sense if the certificate is\n\
                                stored on a PKCS#11 token that requires a login.\n\
                                (802-1x.phase2-client-cert-password)\n\
  --phase2-private-key          Contains the \"phase 2\" inner private key when\n\
                                the \"phase2-auth\" or \"phase2-autheap\" property\n\
                                is set to \"tls\".\n\
                                (802-1x.phase2-private-key)\n\
  --phase2-private-key-password The password used to decrypt the \"phase 2\"\n\
                                private key specified in the\n\
                                \"phase2-private-key\" property when the private\n\
                                key either uses the path scheme, or is a PKCS#12\n\
                                format key. (802-1x.phase2-private-key-password)\n\
  --private-key                 Contains the private key when the \"eap\" property\n\
                                is set to \"tls\". WARNING: \"private-key\" is not a\n\
                                \"secret\" property, and thus unencrypted private\n\
                                key data using the BLOB scheme may be readable\n\
                                by unprivileged users. Private keys should\n\
                                always be encrypted with a private key password\n\
                                to prevent unauthorized access to unencrypted\n\
                                private key data. (802-1x.private-key)\n\
  --private-key-password        The password used to decrypt the private key\n\
                                specified in the \"private-key\" property when the\n\
                                private key either uses the path scheme, or if\n\
                                the private key is a PKCS#12 format key.\n\
                                (802-1x.private-key-password)\n\
  --proactive-key-caching       Boolean to enable Proactive Key Caching, also\n\
                                known as Opportunistic Key Caching (OKC).\n\
                                (802-11-wireless-security.proactive-key-caching)\n\
\n\
  *** WEP ***\n\
  --wep-key                     A string containing the WEP key; can be either 5\n\
                                or 13 hexadecimal bytes (10 or 26 hex chars) or\n\
                                an ASCII string of 5 to 13 characters. WEP key\n\
                                is assumed to be index 0.\n\
                                (802-11-wireless-security.wep-key0)\n\
\n\
  *** Miscellaneous ***\n\
  -a, --activate                Indicates to automatically activate the\n\
                                connection. Optional.\n\
  --autoconnect-retries         The number of times a connection should be tried\n\
                                when autoactivating before giving up. Zero means\n\
                                forever, -1 means the global default (4 times if\n\
                                not overridden). Setting this to 1 means to try\n\
                                activation only once before blocking\n\
                                autoconnect. Note that after a timeout,\n\
                                NetworkManager will try to autoconnect again.\n\
                                (connection.autoconnect-retries)\n\
  --bgscan                      Configures scanning/roaming options\n\
                                (802-11-wireless.bgscan)\n\
  -d, --disable-ipv6            Indicates IPv6 should be disabled on the\n\
                                connection. Optional.\n\
  -h, --hidden                  If TRUE, indicates that the network is a\n\
                                non-broadcasting network that hides its SSID.\n\
                                (802-11-wireless.hidden)\n\
  -o, --open                    Boolean specifying whether or not the AP is an\n\
                                \"open\" network (i.e., no security is used).\n\
  --pairwise                    A list of pairwise encryption algorithms which\n\
                                prevents connections to Wi-Fi networks that do\n\
                                not utilize one of the algorithms in the list.\n\
                                For maximum compatibility leave this property\n\
                                empty. Each list element may be one of \"tkip\" or\n\
                                \"ccmp\". (802-11-wireless-security.pairwise)\n\
  -p, --priority                A number indicating the priority of the\n\
                                connection. A connection can be removed by\n\
                                specifying a priority of '-1'. Optional,\n\
                                default is 0.\n\
  --proto                       List of strings specifying the allowed WPA\n\
                                protocol versions to use. Each element may be\n\
                                one \"wpa\" (allow WPA) or \"rsn\" (allow WPA2/RSN).\n\
                                If not specified, both WPA and RSN connections\n\
                                are allowed. (802-11-wireless-security.proto)\n\
\n\
Check here for more information on the many configuration settings supported by\n\
NetworkManager's command line tool (nmcli):\n\
https://man.archlinux.org/man/nmcli.1"
    exit 1
}

#
# Helper function to configure the 'autoconnect-priority' setting of
# a connection
#
configure_connection_priority() {
    # Update priority
    ${NMCLI} conn modify id ${SSID} connection.autoconnect-priority ${PRIORITY} || cleanup_and_fail "Unable to update connection priority"
}

#
# Helper function to configure the 'autoconnect-retries' setting of
# a connection
#
configure_connection_autoconnect_retries() {
    # Update autoconnect retries
    ${NMCLI} conn modify id ${SSID} connection.autoconnect-retries ${AUTOCONNECT_RETRIES} || cleanup_and_fail "Unable to update connection autoconnect retries"
}

#
# Helper function to configure the 'auth-retries' setting of
# a connection
#
configure_connection_auth_retries() {
    # Update auth retries
    ${NMCLI} conn modify id ${SSID} connection.auth-retries ${AUTH_RETRIES} || cleanup_and_fail "Unable to update connection auth retries"
}

#
# Helper function to configure the IPv6 settings of a connection
#
configure_connection_ipv6() {
    if [ "${DISABLE_IPV6}" == true ]; then
        # Disable IPv6
        ${NMCLI} conn modify id ${SSID} ipv6.ignore-auto-dns false ipv6.never-default false || cleanup_and_fail "Unable to update IPv6 configuration"
    else
        # Enable IPv6
        ${NMCLI} conn modify id ${SSID} ipv6.ignore-auto-dns true ipv6.never-default true || cleanup_and_fail "Unable to update IPv6 configuration"
    fi
    ${NMCLI} conn modify id ${SSID} ipv6.method auto || cleanup_and_fail "Unable to update IPv6 configuration"
}

#
# Helper function to copy a specified file to the NetworkManager
# system-connections folder and assign it the proper file permissions
#
configure_connection_copy_in_file() {
    # Verify file is present
    if [ ! -f "$1" ]; then
        echo "ERROR: Could not find file $1"
        echo ""
        show_usage
    fi

    # Copy in file
    file_basename=$(basename $1)
    cp $1 $NM_SYSTEM_CONNECTIONS_DIR/ || cleanup_and_fail "Could not copy file $1"
    chmod 600 $NM_SYSTEM_CONNECTIONS_DIR/$file_basename || cleanup_and_fail "Could not update permissions on file $file_basename"
}

#
# Helper function to bring up a connection
#
bring_up_connection() {
    # Bring up the connection
    ${NMCLI} conn up ${SSID} || cleanup_and_fail "Unable to bring up connection"
}

#
# Helper function to delete a connection
#
delete_connection() {
    # Delete the connection
    ${NMCLI} conn delete ${SSID} || cleanup_and_fail "Unable to delete connection"
    return $?
}

#
# Helper function to determine if a connection exists
#
connection_exists() {
    # Check if the given connection is in the `nmcli conn show` output
    return $(${NMCLI} conn show "$1" > /dev/null; echo $?)
}

#
# Helper function that echo's proper nmcli connection modification command
# if the 'hidden' parameter is specified
#
hidden_command_builder() {
    # Check for the 'hidden' parameter
    if [ "${HIDDEN}" == true ]; then
        echo "802-11-wireless.hidden 1"
    else
        echo ""
    fi
}

#
# Helper function that echo's proper nmcli connection modification command
# if the 'pairwise' parameter is specified
#
pairwise_command_builder() {
    if [ ! -z "$PAIRWISE" ]; then
        echo "802-11-wireless-security.pairwise $PAIRWISE"
    else
        echo ""
    fi
}

#
# Helper function that echo's proper nmcli connection modification command
# if the 'bgscan' parameter is specified
#
bgscan_command_builder() {
    if [ ! -z "$BGSCAN" ]; then
        echo "802-11-wireless.bgscan \"${BGSCAN}\""
    else
        echo ""
    fi
}

#
# Helper function that echo's proper nmcli connection modification command
# if the 'proto' parameter is specified
#
proto_command_builder() {
    if [ ! -z "$PROTO" ]; then
        echo "802-11-wireless-security.proto $PROTO"
    else
        echo ""
    fi
}

#
# Helper function that echo's proper nmcli connection modification command
# if the 'proactive-key-caching' parameter is specified
#
proactive_key_caching_command_builder() {
    if [ "${PROACTIVE_KEY_CACHING}" == true ]; then
        echo "802-11-wireless-security.proactive-key-caching 1"
    else
        echo ""
    fi
}

#
# Helper function to handle configurations common to any connection type
#
common_connection_config_cleanup() {
    # Update connection priority
    configure_connection_priority

    # Update connection autoconnect retries
    configure_connection_autoconnect_retries

    # Handle IPv6
    configure_connection_ipv6

    if [ "${ACTIVATE}" == true ]; then
        # Automatically activate the new connection
        bring_up_connection
    fi
}

#
# Handle a WPA connection
#
wpa_connection() {
    # Check for improper parameters
    if [ ! -z "$WEP_KEY" ]; then
        echo "ERROR: \"wep-key\" cannot be used with \"psk\""
        echo ""
        show_usage
    fi
    if [ ! -z "$EAP" ]; then
        echo "ERROR: \"eap\" cannot be used with \"psk\""
        echo ""
        show_usage
    fi

    # Create NM connection if necessary
    if ! connection_exists ${SSID}; then
        # Connection doesn't exists
        ${NMCLI} conn add con-name ${SSID} ifname ${WIFI_INTERFACE_NAME} type wifi ssid ${SSID}
    fi

    # Configure security
    cmd="${NMCLI} conn modify id ${SSID} 802-11-wireless-security.key-mgmt wpa-psk 802-11-wireless-security.psk ${PSK}"

    # Check for the following parameters:
    # - 'pairwise'
    # - 'proto'
    # - 'proactive-key-caching'
    # - 'hidden'
    # - 'bgscan'
    cmd="$cmd $(pairwise_command_builder)\
        $(proto_command_builder)\
        $(proactive_key_caching_command_builder)\
        $(hidden_command_builder)\
        $(bgscan_command_builder)"

    # Run command
    eval $cmd

    common_connection_config_cleanup
}

#
# Handle a WEP connection
#
wep_connection() {
    # Check for improper parameters
    if [ ! -z "$EAP" ]; then
        echo "ERROR: \"eap\" cannot be used with \"wep-key\""
        echo ""
        show_usage
    fi
    if [ ! -z "$PSK" ]; then
        echo "ERROR: \"psk\" cannot be used with \"wep-key\""
        echo ""
        show_usage
    fi

    # Create NM connection if necessary
    if ! connection_exists ${SSID}; then
        # Connection doesn't exists
        ${NMCLI} conn add con-name ${SSID} ifname ${WIFI_INTERFACE_NAME} type wifi ssid ${SSID}
    fi

    # Configure security
    cmd="${NMCLI} conn modify id ${SSID} 802-11-wireless-security.key-mgmt none 802-11-wireless-security.wep-key0 ${WEP_KEY}"  # Assume WEP key index 0

    # Check for the following parameters:
    # - 'pairwise'
    # - 'proto'
    # - 'proactive-key-caching'
    # - 'hidden'
    # - 'bgscan'
    cmd="$cmd $(pairwise_command_builder)\
        $(proto_command_builder)\
        $(proactive_key_caching_command_builder)\
        $(hidden_command_builder)\
        $(bgscan_command_builder)"

    # Run command
    eval $cmd

    common_connection_config_cleanup
}

#
# Handle a EAP connection
#
eap_connection() {
    # Check for improper parameters
    if [ ! -z "$WEP_KEY" ]; then
        echo "ERROR: \"wep-key\" cannot be used with \"eap\""
        echo ""
        show_usage
    fi
    if [ ! -z "$PSK" ]; then
        echo "ERROR: \"psk\" cannot be used with \"eap\""
        echo ""
        show_usage
    fi

    # Link in the FS key
    keyctl link @us @s

    # Create NM connection if necessary
    if ! connection_exists ${SSID}; then
        # Connection doesn't exists
        ${NMCLI} conn add con-name ${SSID} ifname ${WIFI_INTERFACE_NAME} type wifi ssid ${SSID}
    fi

    # Configure security
    cmd="${NMCLI} conn modify id ${SSID} 802-1x.eap ${EAP} 802-11-wireless-security.key-mgmt wpa-eap"

    # Check for the 'identity' parameter
    if [ ! -z "$IDENTITY" ]; then
        cmd="$cmd 802-1x.identity ${IDENTITY}"
    fi

    # Check for the 'anonymous-identity' parameter
    if [ ! -z "$ANONYMOUS_IDENTITY" ]; then
        cmd="$cmd 802-1x.anonymous-identity ${ANONYMOUS_IDENTITY}"
    fi

    # Check for the 'password' parameter
    if [ ! -z "$PASSWORD" ]; then
        cmd="$cmd 802-1x.password ${PASSWORD}"
    fi

    # Check for the 'phase1-fast-provisioning' parameter
    if [ ! -z "$PHASE1_FAST_PROVISIONING" ]; then
        cmd="$cmd 802-1x.phase1-fast-provisioning ${PHASE1_FAST_PROVISIONING}"
    fi

    # Check for the 'phase2-auth' parameter
    if [ ! -z "$PHASE2_AUTH" ]; then
        cmd="$cmd 802-1x.phase2-auth ${PHASE2_AUTH}"
    fi

    # Check for the 'phase2-autheap' parameter
    if [ ! -z "$PHASE2_AUTHEAP" ]; then
        cmd="$cmd 802-1x.phase2-autheap ${PHASE2_AUTHEAP}"
    fi

    # Check for the 'phase2-ca-cert' parameter
    if [ ! -z "$PHASE2_CA_CERT" ]; then
        # Copy in phase 2 CA certificate file
        configure_connection_copy_in_file $PHASE2_CA_CERT

        cmd="$cmd 802-1x.phase2-ca-cert ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $PHASE2_CA_CERT)"
    fi

    # Check for the 'phase2-ca-cert-password' parameter
    if [ ! -z "$PHASE2_CA_CERT_PASSWORD" ]; then
        cmd="$cmd 802-1x.phase2-ca-cert-password ${PHASE2_CA_CERT_PASSWORD}"
    fi

    # Check for the 'phase2-client-cert' parameter
    if [ ! -z "$PHASE2_CLIENT_CERT" ]; then
        # Copy in phase 2 client certificate file
        configure_connection_copy_in_file $PHASE2_CLIENT_CERT

        cmd="$cmd 802-1x.phase2-client-cert ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $PHASE2_CLIENT_CERT)"
    fi

    # Check for the 'phase2-client-cert-password' parameter
    if [ ! -z "$PHASE2_CLIENT_CERT_PASSWORD" ]; then
        cmd="$cmd 802-1x.phase2-client-cert-password ${PHASE2_CLIENT_CERT_PASSWORD}"
    fi

    # Check for the 'phase2-private-key' parameter
    if [ ! -z "$PHASE2_PRIVATE_KEY" ]; then
        # Copy in phase 2 private key file
        configure_connection_copy_in_file $PHASE2_PRIVATE_KEY

        cmd="$cmd 802-1x.phase2-private-key ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $PHASE2_PRIVATE_KEY)"
    fi

    # Check for the 'phase2-private-key-password' parameter
    if [ ! -z "$PHASE2_PRIVATE_KEY_PASSWORD" ]; then
        cmd="$cmd 802-1x.phase2-private-key-password ${PHASE2_PRIVATE_KEY_PASSWORD}"
    fi

    # Check for the 'ca-cert' parameter
    if [ ! -z "$CA_CERT" ]; then
        # Copy in CA certificate file
        configure_connection_copy_in_file $CA_CERT

        cmd="$cmd 802-1x.ca-cert ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $CA_CERT)"
    fi

    # Check for the 'ca-cert-password' parameter
    if [ ! -z "$CA_CERT_PASSWORD" ]; then
        cmd="$cmd 802-1x.ca-cert-password ${CA_CERT_PASSWORD}"
    fi

    # Check for the 'client-cert' parameter
    if [ ! -z "$CLIENT_CERT" ]; then
        # Copy in client certificate file
        configure_connection_copy_in_file $CLIENT_CERT

        cmd="$cmd 802-1x.client-cert ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $CLIENT_CERT)"
    fi

    # Check for the 'client-cert-password' parameter
    if [ ! -z "$CLIENT_CERT_PASSWORD" ]; then
        cmd="$cmd 802-1x.client-cert-password ${CLIENT_CERT_PASSWORD}"
    fi

    # Check for the 'private-key' parameter
    if [ ! -z "$PRIVATE_KEY" ]; then
        # Copy in private key file
        configure_connection_copy_in_file $PRIVATE_KEY

        cmd="$cmd 802-1x.private-key ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $PRIVATE_KEY)"
    fi

    # Check for the 'private-key-password' parameter
    if [ ! -z "$PRIVATE_KEY_PASSWORD" ]; then
        cmd="$cmd 802-1x.private-key-password ${PRIVATE_KEY_PASSWORD}"
    fi

    # Check for the 'pac-file' parameter
    if [ ! -z "$PAC_FILE" ]; then
        # Copy in PAC file
        configure_connection_copy_in_file $PAC_FILE

        cmd="$cmd 802-1x.pac-file ${NM_SYSTEM_CONNECTIONS_DIR}/$(basename $PAC_FILE)"
    fi

    # Check for the 'pac-file-password' parameter
    if [ ! -z "$PAC_FILE_PASSWORD" ]; then
        cmd="$cmd 802-1x.pac-file-password ${PAC_FILE_PASSWORD}"
    fi

    # Check for the following parameters:
    # - 'pairwise'
    # - 'proto'
    # - 'proactive-key-caching'
    # - 'hidden'
    # - 'bgscan'
    cmd="$cmd $(pairwise_command_builder)\
        $(proto_command_builder)\
        $(proactive_key_caching_command_builder)\
        $(hidden_command_builder)\
        $(bgscan_command_builder)"

    # Run command
    eval $cmd

    # Configure auth retries
    configure_connection_auth_retries

    common_connection_config_cleanup
}

#
# Handle an open connection
#
open_connection() {
    # Create NM connection if necessary
    if ! connection_exists ${SSID}; then
        # Connection doesn't exists
        ${NMCLI} conn add con-name ${SSID} ifname ${WIFI_INTERFACE_NAME} type wifi ssid ${SSID}
    fi

    # Configure connection
    cmd="${NMCLI} conn modify id ${SSID} 802-11-wireless.ssid ${SSID}"

    # Check for the following parameters:
    # - 'hidden'
    # - 'bgscan'
    cmd="$cmd $(hidden_command_builder) $(bgscan_command_builder)"

    # Run command
    eval $cmd

    common_connection_config_cleanup
}

# Parse parameters
TEMP=`getopt -o p:dahos: \
        -l ssid:,psk:,eap:,identity:,anonymous-identity:,password:,phase2-auth:,phase2-autheap:,phase2-ca-cert:,phase2-ca-cert-password:,phase2-client-cert:,phase2-client-cert-password:,phase2-private-key:,phase2-private-key-password:,ca-cert:,ca-cert-password:,client-cert:,client-cert-password:,phase1-fast-provisioning:,private-key:,private-key-password:,pac-file:,wep-key:,pairwise:,proto:,proactive-key-caching,bgscan:,hidden,priority:,disable-ipv6,activate,open,auth-retries:,autoconnect-retries:,pac-file-password: \
        -n 'ig60_wifi_config' -- "$@"`

if [ $? != 0 ] ; then
    echo "ERROR: Unable to parse parameters"
    echo ""
    show_usage
fi

# Note the quotes around `$TEMP`: they are essential!
eval set -- "$TEMP"

### Variables ###
# Common
SSID=

# WPA
PSK=

# Enterprise (802.1x)
EAP=
IDENTITY=
ANONYMOUS_IDENTITY=
AUTH_RETRIES=-1                 # Default is -1 according to NM documentation
PASSWORD=
PHASE2_AUTH=
PHASE2_AUTHEAP=
PHASE2_CA_CERT=
PHASE2_CA_CERT_PASSWORD=
PHASE2_CLIENT_CERT=
PHASE2_CLIENT_CERT_PASSWORD=
PHASE2_PRIVATE_KEY=
PHASE2_PRIVATE_KEY_PASSWORD=
CA_CERT=
CA_CERT_PASSWORD=
CLIENT_CERT=
CLIENT_CERT_PASSWORD=
PRIVATE_KEY=
PRIVATE_KEY_PASSWORD=
PAC_FILE=
PAC_FILE_PASSWORD=
PHASE1_FAST_PROVISIONING=
PROACTIVE_KEY_CACHING=false

# WEP
WEP_KEY=

# Miscellaneous
PAIRWISE=
HIDDEN=false
PROTO=
BGSCAN=
OPEN=false
PRIORITY=0                      # Default priority is 0 if not specified
DISABLE_IPV6=false              # Enable IPv6 by default
ACTIVATE=false                  # Automatically connect to the new connection
AUTOCONNECT_RETRIES=-1          # Default is -1 according to NM documentation

while true; do
    case "$1" in
        -s | --ssid ) SSID="$2"; shift 2 ;;
        --psk ) PSK="$2"; shift 2 ;;
        --eap ) EAP="$2"; shift 2 ;;
        --identity ) IDENTITY="$2"; shift 2 ;;
        --anonymous-identity ) ANONYMOUS_IDENTITY="$2"; shift 2 ;;
        --auth-retries ) AUTH_RETRIES="$2"; shift 2 ;;
        --password ) PASSWORD="$2"; shift 2 ;;
        --phase1-fast-provisioning ) PHASE1_FAST_PROVISIONING="$2"; shift 2 ;;
        --proactive-key-caching ) PROACTIVE_KEY_CACHING=true; shift ;;
        --phase2-auth ) PHASE2_AUTH="$2"; shift 2 ;;
        --phase2-autheap ) PHASE2_AUTHEAP="$2"; shift 2 ;;
        --phase2-ca-cert ) PHASE2_CA_CERT="$2"; shift 2 ;;
        --phase2-ca-cert-password ) PHASE2_CA_CERT_PASSWORD="$2"; shift 2 ;;
        --phase2-client-cert ) PHASE2_CLIENT_CERT="$2"; shift 2 ;;
        --phase2-client-cert-password ) PHASE2_CLIENT_CERT_PASSWORD="$2"; shift 2 ;;
        --phase2-private-key ) PHASE2_PRIVATE_KEY="$2"; shift 2 ;;
        --phase2-private-key-password ) PHASE2_PRIVATE_KEY_PASSWORD="$2"; shift 2 ;;
        --ca-cert ) CA_CERT="$2"; shift 2 ;;
        --ca-cert-password ) CA_CERT_PASSWORD="$2"; shift 2 ;;
        --client-cert ) CLIENT_CERT="$2"; shift 2 ;;
        --client-cert-password ) CLIENT_CERT_PASSWORD="$2"; shift 2 ;;
        --private-key ) PRIVATE_KEY="$2"; shift 2 ;;
        --private-key-password ) PRIVATE_KEY_PASSWORD="$2"; shift 2 ;;
        --pac-file ) PAC_FILE="$2"; shift 2 ;;
        --pac-file-password ) PAC_FILE_PASSWORD="$2"; shift 2 ;;
        --wep-key ) WEP_KEY="$2"; shift 2 ;;
        --pairwise ) PAIRWISE="$2"; shift 2 ;;
        -h | --hidden ) HIDDEN=true; shift ;;
        --proto ) PROTO="$2"; shift 2 ;;
        --bgscan ) BGSCAN="$2"; shift 2 ;;
        -p | --priority ) PRIORITY="$2"; shift 2 ;;
        -d | --disable-ipv6 ) DISABLE_IPV6=true; shift ;;
        -a | --activate ) ACTIVATE=true; shift ;;
        --autoconnect-retries ) AUTOCONNECT_RETRIES="$2"; shift 2 ;;
        -o | --open ) OPEN=true; shift ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done

# Check for SSID
if [ -z "$SSID" ]; then
    echo "ERROR: \"ssid\" must be specified"
    echo ""
    show_usage
fi

# Check that 'priority', 'autoconnect-retries', and 'auth-retries' are numbers
re='^[+-]?[0-9]+([.][0-9]+)?$'
if ! [[ $PRIORITY =~ $re ]] ; then
    echo "ERROR: \"priority\" must be a number"
    echo ""
    show_usage
fi
if ! [[ $AUTOCONNECT_RETRIES =~ $re ]] ; then
    echo "ERROR: \"autoconnect-retries\" must be a number"
    echo ""
    show_usage
fi
if ! [[ $AUTH_RETRIES =~ $re ]] ; then
    echo "ERROR: \"auth-retries\" must be a number"
    echo ""
    show_usage
fi

# Check if 'priority' is negative
if [ "$PRIORITY" -lt 0 ]; then
    # 'Priority' is negative, so delete the connection
    delete_connection
    exit $?
fi

if [ ! -z "$PSK" ]; then
    # WPA
    wpa_connection
elif [ ! -z "$WEP_KEY" ]; then
    # WEP
    wep_connection
elif [ ! -z "$EAP" ]; then
    # Enterprise
    eap_connection
elif [ "${OPEN}" == true ]; then
    # Open network (no security)
    open_connection
else
    # Error, show usage
    echo "Incorrect parameters"
    show_usage
fi

exit 0
