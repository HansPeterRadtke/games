using System;
using System.IO;
using System.Runtime.InteropServices;

namespace HPR.BuildSceneGate
{
    /// <summary>
    /// Reject special files before a potentially blocking file open. This check
    /// assumes stable local inputs; it does not protect against a hostile process
    /// replacing a path between this inspection and the subsequent read.
    /// </summary>
    internal static class RegularFileInput
    {
        private const int AtCurrentDirectory = -100;
        private const int NoFollowOrAutomount = 0x100 | 0x800;
        private const uint StatxType = 0x1;
        private const ushort FileTypeMask = 0xf000;
        private const ushort RegularFileType = 0x8000;

        // Linux UAPI linux/stat.h: the statx buffer is 0x100 bytes, stx_mask is
        // at 0x00, and stx_mode is at 0x1c. Other fields are deliberately unused.
        // https://man7.org/linux/man-pages/man2/statx.2.html
        [StructLayout(LayoutKind.Explicit, Size = 256)]
        private struct StatxBuffer
        {
            [FieldOffset(0)] public uint Mask;
            [FieldOffset(28)] public ushort Mode;
        }

        [DllImport("libc", EntryPoint = "statx", SetLastError = true)]
        private static extern int ReadStatx(int directory,
            [MarshalAs(UnmanagedType.LPUTF8Str)] string path,
            int flags, uint mask, out StatxBuffer result);

        internal static void RequireRegular(string path)
        {
            if (!RuntimeInformation.IsOSPlatform(OSPlatform.Linux) ||
                RuntimeInformation.ProcessArchitecture != Architecture.X64)
                throw new NotSupportedException(
                    "Local input file validation currently supports Linux x86-64 only.");
            if (string.IsNullOrEmpty(path) || path.IndexOf('\0') >= 0)
                throw new InvalidDataException("Invalid local input file path.");

            StatxBuffer result;
            int status;
            try
            {
                status = ReadStatx(AtCurrentDirectory, path, NoFollowOrAutomount, StatxType, out result);
            }
            catch (DllNotFoundException e)
            {
                throw new NotSupportedException("Local input validation requires the Linux statx API.", e);
            }
            catch (EntryPointNotFoundException e)
            {
                throw new NotSupportedException("Local input validation requires the Linux statx API.", e);
            }

            if (status != 0)
            {
                int error = Marshal.GetLastWin32Error();
                throw new IOException("Cannot inspect local input file (native error " + error + "): " + path);
            }
            if ((result.Mask & StatxType) == 0)
                throw new NotSupportedException("The filesystem did not report the input file type: " + path);
            if ((result.Mode & FileTypeMask) != RegularFileType)
                throw new InvalidDataException("Input must be an ordinary local file: " + path);
        }
    }
}
