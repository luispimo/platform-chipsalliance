# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import join

from platformio.managers.platform import PlatformBase


class ChipsalliancePlatform(PlatformBase):
    def get_boards(self, id_=None):
        result = PlatformBase.get_boards(self, id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key, value in result.items():
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        if "tools" not in debug:
            debug["tools"] = {}

        tools = (
            "digilent-hs1",
            "olimex-arm-usb-tiny-h",
            "olimex-arm-usb-ocd-h",
            "olimex-arm-usb-ocd",
            "olimex-jtag-tiny",
            "verilator",
            "whisper",
        )
        for tool in tools:
            if tool in debug["tools"]:
                continue
            if tool == "whisper":
                debug['tools'][tool] = {
                    "init_cmds": [
                        "set arch riscv:rv32",
                        "target extended-remote $DEBUG_PORT",
                        "$INIT_BREAK",
                        "$LOAD_CMDS",
                    ],
                    "server": {
                        "package": "framework-wd-riscv-sdk",
                        "arguments": [
                            "--gdb",
                            "--gdb-tcp-port=3333",
                            "--configfile=$PACKAGE_DIR/board/whisper/whisper_eh1.json",
                            "$PROJECT_DIR/.pio/build/swervolf_nexys/firmware.elf"
                        ],
                        "executable": "board/whisper/whisper"
                    },
                    "onboard": True
                }
                continue
            server_args = [
                "-s",
                join(
                    self.get_package_dir("framework-wd-riscv-sdk") or "",
                    "board",
                    board.get("build.variant", ""),
                ),
                "-s",
                "$PACKAGE_DIR/share/openocd/scripts",
            ]
            if tool == "verilator":
                openocd_config = join(
                    self.get_dir(),
                    "misc",
                    "openocd",
                    board.get("debug.openocd_board", "swervolf_sim.cfg"),
                )
                server_args.extend(["-f", openocd_config])
            elif debug.get("openocd_config"):
                server_args.extend(["-f", debug.get("openocd_config")])
            else:
                assert debug.get("openocd_target"), (
                    "Missing target configuration for %s" % board.id
                )
                # All tools are FTDI based
                server_args.extend(
                    [
                        "-f",
                        "interface/ftdi/%s.cfg" % tool,
                        "-f",
                        "target/%s.cfg" % debug.get("openocd_target"),
                    ]
                )
            debug["tools"][tool] = {
                "init_cmds": [
                    "define pio_reset_halt_target",
                    "   monitor reset halt",
                    "end",
                    "define pio_reset_run_target",
                    "   monitor reset",
                    "end",
                    "set mem inaccessible-by-default off",
                    "set arch riscv:rv32",
                    "set remotetimeout 250",
                    "target extended-remote $DEBUG_PORT",
                    "$INIT_BREAK",
                    "$LOAD_CMDS",
                ],
                "server": {
                    "package": "tool-openocd-riscv-chipsalliance",
                    "executable": "bin/openocd",
                    "arguments": server_args,
                },
                "onboard": tool in debug.get("onboard_tools", [])
                or tool == "verilator",
            }

        board.manifest["debug"] = debug
        return board
