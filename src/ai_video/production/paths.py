from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


def resolve_contained_path(
    project_root: Path,
    stored: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    if stored.is_absolute() or ".." in stored.parts:
        raise ValueError(f"Path must be clean and project-relative: {stored}")
    try:
        root = project_root.resolve()
        boundary = (allowed_root or root).resolve()
        resolved = (root / stored).resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Path could not be resolved safely: {stored}") from exc
    try:
        boundary.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Allowed root escapes project root: {boundary}") from exc
    try:
        resolved.relative_to(boundary)
    except ValueError as exc:
        raise ValueError(f"Path escapes allowed root: {stored}") from exc
    return resolved


@dataclass(frozen=True)
class NoFollowFile:
    data: bytes
    file_sha256: str
    size_bytes: int
    mode: int
    device: int
    inode: int


@dataclass(frozen=True)
class VerifiedRenderFile:
    path: Path
    fd: int
    created_stat: os.stat_result


def _contained_relative(path: Path, contained_by: Path) -> tuple[Path, Path, Path]:
    path = Path(path)
    root = Path(contained_by)
    if not path.is_absolute() or not root.is_absolute():
        raise ValueError("P3 artifact paths and containment roots must be absolute.")
    if ".." in path.parts or ".." in root.parts:
        raise ValueError("P3 artifact paths must be lexically clean.")
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"P3 artifact path escapes its boundary: {path}") from exc
    return path, root, relative


def _validate_new_contained_root(
    root: Path,
    *,
    allowed_parent: Path,
) -> Path:
    root, parent, relative = _contained_relative(root, allowed_parent)
    if not relative.parts:
        raise ValueError("P3 staging root must be below its allowed parent.")
    with _open_directory_nofollow(root.parent, contained_by=parent):
        try:
            os.lstat(root)
        except FileNotFoundError:
            return root
    raise ValueError(f"P3 staging root must not already exist: {root}")


def _validate_contained_target(
    root: Path,
    relative: Path,
    *,
    before_creation: bool,
) -> Path:
    root = Path(root)
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        raise ValueError("P3 target must be a clean relative file path.")
    target, _, target_relative = _contained_relative(root / relative, root)
    if not target_relative.parts:
        raise ValueError("P3 target cannot be the source root.")
    if root.exists():
        with _open_directory_nofollow(target.parent, contained_by=root):
            exists = False
            try:
                os.lstat(target)
                exists = True
            except FileNotFoundError:
                pass
            if before_creation and exists:
                raise ValueError(f"P3 target already exists: {target}")
            if not before_creation and not exists:
                raise ValueError(f"P3 target does not exist: {target}")
    elif not before_creation:
        raise ValueError(f"P3 source root does not exist: {root}")
    return target


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _revalidate_held_directory_chain(
    directory: Path,
    *,
    root: Path,
    relative: Path,
    descriptors: list[int],
) -> None:
    root_lstat = os.lstat(root)
    if (
        stat.S_ISLNK(root_lstat.st_mode)
        or not stat.S_ISDIR(root_lstat.st_mode)
        or not _same_file(root_lstat, os.fstat(descriptors[0]))
    ):
        raise ValueError(f"P3 containment root changed during traversal: {root}")
    for index, component in enumerate(relative.parts, start=1):
        current = os.stat(
            component,
            dir_fd=descriptors[index - 1],
            follow_symlinks=False,
        )
        held = os.fstat(descriptors[index])
        if (
            stat.S_ISLNK(current.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or not _same_file(current, held)
        ):
            raise ValueError(f"P3 directory changed during traversal: {directory}")


@contextmanager
def _open_directory_nofollow(
    directory: Path,
    *,
    contained_by: Path,
) -> Iterator[int]:
    directory, root, relative = _contained_relative(directory, contained_by)
    descriptors: list[int] = []
    traversal_complete = False
    try:
        root_lstat = os.lstat(root)
        if stat.S_ISLNK(root_lstat.st_mode) or not stat.S_ISDIR(root_lstat.st_mode):
            raise ValueError(f"P3 containment root must be a non-symlink directory: {root}")
        descriptors.append(os.open(root, _directory_flags()))
        if not _same_file(root_lstat, os.fstat(descriptors[-1])):
            raise ValueError(f"P3 containment root changed during traversal: {root}")
        for component in relative.parts:
            component_lstat = os.stat(
                component,
                dir_fd=descriptors[-1],
                follow_symlinks=False,
            )
            if stat.S_ISLNK(component_lstat.st_mode) or not stat.S_ISDIR(
                component_lstat.st_mode
            ):
                raise ValueError(
                    f"P3 path component must be a non-symlink directory: {directory}"
                )
            descriptor = os.open(component, _directory_flags(), dir_fd=descriptors[-1])
            descriptors.append(descriptor)
            if not _same_file(component_lstat, os.fstat(descriptor)):
                raise ValueError(f"P3 directory changed during traversal: {directory}")
        traversal_complete = True
        yield descriptors[-1]
    finally:
        revalidation_error: BaseException | None = None
        if traversal_complete:
            try:
                _revalidate_held_directory_chain(
                    directory,
                    root=root,
                    relative=relative,
                    descriptors=descriptors,
                )
            except BaseException as exc:
                revalidation_error = exc
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except BaseException as exc:
                if revalidation_error is None:
                    revalidation_error = exc
        if revalidation_error is not None:
            raise revalidation_error


@contextmanager
def _open_regular_file_nofollow(
    path: Path,
    *,
    contained_by: Path,
) -> Iterator[tuple[int, os.stat_result]]:
    path, root, relative = _contained_relative(path, contained_by)
    if not relative.parts:
        raise ValueError("P3 regular-file path cannot be the containment root.")
    descriptor: int | None = None
    with _open_directory_nofollow(path.parent, contained_by=root) as parent_descriptor:
        before = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError(f"P3 artifact must be a non-symlink regular file: {path}")
        try:
            descriptor = os.open(
                path.name,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=parent_descriptor,
            )
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or not _same_file(before, opened):
                raise ValueError(f"P3 artifact changed during open: {path}")
            current = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
            if not _same_file(current, opened):
                raise ValueError(f"P3 artifact changed during inspection: {path}")
            yield descriptor, opened
            final = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
            if not _same_file(final, os.fstat(descriptor)):
                raise ValueError(f"P3 artifact changed during inspection: {path}")
        finally:
            if descriptor is not None:
                os.close(descriptor)


def _read_regular_file_nofollow(path: Path, *, contained_by: Path) -> NoFollowFile:
    with _open_regular_file_nofollow(path, contained_by=contained_by) as (
        descriptor,
        opened,
    ):
        chunks: list[bytes] = []
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
            digest.update(chunk)
        final = os.fstat(descriptor)
        if not _same_file(opened, final) or final.st_size != sum(map(len, chunks)):
            raise ValueError(f"P3 artifact changed while it was read: {path}")
        return NoFollowFile(
            data=b"".join(chunks),
            file_sha256=digest.hexdigest(),
            size_bytes=final.st_size,
            mode=final.st_mode,
            device=final.st_dev,
            inode=final.st_ino,
        )


def _create_directory_nofollow(
    directory: Path,
    *,
    contained_by: Path,
    mode: int = 0o700,
) -> Path:
    directory, root, relative = _contained_relative(directory, contained_by)
    if not relative.parts:
        raise ValueError("P3 cannot create the containment root itself.")
    with _open_directory_nofollow(directory.parent, contained_by=root) as parent_descriptor:
        os.mkdir(directory.name, mode=mode, dir_fd=parent_descriptor)
        before = os.stat(directory.name, dir_fd=parent_descriptor, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            raise ValueError(f"P3 created path is not a regular directory: {directory}")
        descriptor = os.open(directory.name, _directory_flags(), dir_fd=parent_descriptor)
        try:
            if not _same_file(before, os.fstat(descriptor)):
                raise ValueError(f"P3 created directory changed during validation: {directory}")
            os.fsync(descriptor)
            os.fsync(parent_descriptor)
        finally:
            os.close(descriptor)
    return directory


def _create_regular_file_nofollow(
    path: Path,
    *,
    data: bytes,
    contained_by: Path,
    mode: int = 0o600,
) -> NoFollowFile:
    path, root, relative = _contained_relative(path, contained_by)
    if not relative.parts:
        raise ValueError("P3 cannot create a regular file at the containment root.")
    with _open_directory_nofollow(path.parent, contained_by=root) as parent_descriptor:
        descriptor = os.open(
            path.name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW,
            mode,
            dir_fd=parent_descriptor,
        )
        try:
            view = memoryview(data)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fsync(descriptor)
            created = os.fstat(descriptor)
            current = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
            if (
                not stat.S_ISREG(created.st_mode)
                or not _same_file(created, current)
                or created.st_size != len(data)
            ):
                raise ValueError(f"P3 created file failed validation: {path}")
            os.fsync(parent_descriptor)
            return NoFollowFile(
                data=data,
                file_sha256=hashlib.sha256(data).hexdigest(),
                size_bytes=created.st_size,
                mode=created.st_mode,
                device=created.st_dev,
                inode=created.st_ino,
            )
        finally:
            os.close(descriptor)


@contextmanager
def _copy_held_fd_to_regular_file_nofollow(
    source_fd: int,
    destination: Path,
    *,
    contained_by: Path,
    mode: int = 0o600,
) -> Iterator[VerifiedRenderFile]:
    destination, root, relative = _contained_relative(destination, contained_by)
    if not relative.parts:
        raise ValueError("P3 cannot create a verification file at the containment root.")
    source_offset = os.lseek(source_fd, 0, os.SEEK_CUR)
    descriptor: int | None = None
    try:
        with _open_directory_nofollow(
            destination.parent, contained_by=root
        ) as parent_descriptor:
            descriptor = os.open(
                destination.name,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW,
                mode,
                dir_fd=parent_descriptor,
            )
            os.lseek(source_fd, 0, os.SEEK_SET)
            copied = 0
            while chunk := os.read(source_fd, 1024 * 1024):
                view = memoryview(chunk)
                while view:
                    written = os.write(descriptor, view)
                    copied += written
                    view = view[written:]
            os.fsync(descriptor)
            created = os.fstat(descriptor)
            current = os.stat(
                destination.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(created.st_mode)
                or not _same_file(created, current)
                or created.st_size != copied
            ):
                raise ValueError(
                    f"P3 verification copy failed same-file validation: {destination}"
                )
            os.fsync(parent_descriptor)
            os.lseek(descriptor, 0, os.SEEK_SET)
            os.lseek(source_fd, source_offset, os.SEEK_SET)
            yield VerifiedRenderFile(
                path=destination,
                fd=descriptor,
                created_stat=created,
            )
    finally:
        os.lseek(source_fd, source_offset, os.SEEK_SET)
        if descriptor is not None:
            os.close(descriptor)


def _list_regular_files_nofollow(root: Path) -> set[Path]:
    root = Path(root)
    files: set[Path] = set()

    def visit(descriptor: int, relative: Path) -> None:
        for name in sorted(os.listdir(descriptor)):
            entry = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            entry_relative = relative / name
            if stat.S_ISLNK(entry.st_mode):
                raise ValueError(f"P3 source tree contains a symlink: {entry_relative}")
            if stat.S_ISREG(entry.st_mode):
                files.add(entry_relative)
                continue
            if not stat.S_ISDIR(entry.st_mode):
                raise ValueError(
                    f"P3 source tree contains a non-regular entry: {entry_relative}"
                )
            child = os.open(name, _directory_flags(), dir_fd=descriptor)
            try:
                if not _same_file(entry, os.fstat(child)):
                    raise ValueError(
                        f"P3 source directory changed during traversal: {entry_relative}"
                    )
                visit(child, entry_relative)
                current = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if not _same_file(current, os.fstat(child)):
                    raise ValueError(
                        f"P3 source directory changed during traversal: {entry_relative}"
                    )
            finally:
                os.close(child)

    with _open_directory_nofollow(root, contained_by=root) as descriptor:
        visit(descriptor, Path())
    return files
