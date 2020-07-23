import os

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()

FIRMWARE_DIR = platform.get_package_dir("framework-wd-riscv-sdk")
assert os.path.isdir(FIRMWARE_DIR)

board = env.BoardConfig()
variant_dir = os.path.join(FIRMWARE_DIR, "board", board.get("build.variant", ""))

env.SConscript("_bare.py")

env.Append(
    CCFLAGS=[
        "-fno-builtin-printf",
    ],

    CPPDEFINES=[
        ("D_TICK_TIME_MS", 4),
        ("D_ISR_STACK_SIZE", 400),
        "D_BARE_METAL",
        "D_NEXYS_A7",                                       # Nexys A& board 
        "D_SWERV_EH1",                                      # EH1 defines
        ("D_MTIME_ADDRESS","0x8000102"),                    # MTIME address
        ("D_MTIMECMP_ADDRESS","0x80001028"),                # MTIMECMP address
        ("D_CLOCK_RATE","50000000"),                        # Clock rate = 50Mhz   
        ("D_PIC_BASE_ADDRESS","0xf00c0000"),                # PIC base address
        ("D_PIC_NUM_OF_EXT_INTERRUPTS","256"),              # Number of external interrupts = 256
        ("D_EXT_INTERRUPT_FIRST_SOURCE_USED","0"),          # First external interrupt = 0
        ("D_EXT_INTERRUPT_LAST_SOURCE_USED","255"),         # Last external interrupt =  255
        ("D_EXT_INTS_GENERATION_REG_ADDRESS","0x8000100B"), # Register for settup and generation of external interrupts on SweRVolf FPGA
        ("D_TIMER_DURATION_SETUP_ADDRESS","0x80001030"),    # Register for duration setup of a timer on SweRVolf FPGA
        ("D_TIMER_ACTIVATION_ADDRESS","0x80001034"),        # Register for activation of a timer on SweRVolf FPGA  
        ("D_NMI_VEC_ADDRESSS","0x8000100C")                 # nmi_vec address on SweRVolf FPGA
    ],

    CPPPATH=[
        "$PROJECT_SRC_DIR",
        os.path.join(FIRMWARE_DIR, "common", "api_inc"),
        os.path.join(FIRMWARE_DIR, "psp", "api_inc"),
    ],

    LIBPATH=[variant_dir],

    LIBS=["c", "gcc"]
)

# Only for C/C++ sources
env.Append(CCFLAGS=["-include", "sys/cdefs.h"])

if not board.get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH="link.lds")

#
# Target: Build libraries
#

libs = []

if "build.variant" in board:
    env.Append(CPPPATH=[variant_dir, os.path.join(variant_dir, "bsp")])
    libs.append(env.BuildLibrary(os.path.join("$BUILD_DIR", "BoardBSP"), variant_dir))

libs.extend([
    env.BuildLibrary(
        os.path.join("$BUILD_DIR", "PSP"),
        os.path.join(FIRMWARE_DIR, "psp"),
        src_filter=[
            "-<*>",
            "+<psp_ext_interrupts_swerv_eh1.c>",
            "+<psp_traps_interrupts.c>",
            "+<psp_timers.c>",
            "+<psp_performance_monitor_eh1.c>",
            "+<psp_int_vect_swerv_eh1.S>"
        ],
    )
])

env.Prepend(LIBS=libs)
