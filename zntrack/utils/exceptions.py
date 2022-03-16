"""Description: ZnTrack custom exceptions"""


class DescriptorMissing(Exception):
    pass


class DVCProcessError(Exception):
    """DVC specific message for CalledProcessError"""
