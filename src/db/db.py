"""
Database integration module for IDMAP using Prisma Client Python & Neon DB.
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from prisma import Prisma
    prisma = Prisma()
except ImportError:
    prisma = None


async def connect_db():
    """Connect to Neon DB via Prisma Client."""
    if prisma is not None and not prisma.is_connected():
        await prisma.connect()


async def disconnect_db():
    """Disconnect from Neon DB."""
    if prisma is not None and prisma.is_connected():
        await prisma.disconnect()


def get_db():
    """Dependency getter for Prisma Client."""
    return prisma
