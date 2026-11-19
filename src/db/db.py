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
    """Connect to Neon DB via Prisma Client with graceful offline fallback."""
    if prisma is not None and not prisma.is_connected():
        try:
            await prisma.connect()
        except Exception as e:
            print(f"Warning: Neon DB connection failed (falling back to in-memory/CSV mode): {e}")
        except BaseException as e:
            print(f"Warning: Prisma engine could not connect: {e}")


async def disconnect_db():
    """Disconnect from Neon DB."""
    if prisma is not None and prisma.is_connected():
        await prisma.disconnect()


async def reconnect_db():
    """Recycles dropped connections after serverless idle timeouts from Neon PgBouncer pooler."""
    global prisma
    if prisma is not None:
        try:
            if prisma.is_connected():
                await prisma.disconnect()
        except Exception:
            pass
        try:
            await prisma.connect()
        except Exception as e:
            print(f"Warning: Neon DB auto-reconnect failed: {e}")


def get_db():
    """Dependency getter for Prisma Client."""
    return prisma
