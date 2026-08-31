import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermission;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public final class OutputWorkspaceTest {
  private static int assertions = 0;

  public static void main(String[] args) throws Exception {
    createsOnlyTheConfinedWorkspace();
    rejectsInvalidConfigurationShapes();
    rejectsUnsafeAndUnknownProjectIds();
    rejectsUnavailableBaseDirectories();
    rejectsUnwritableBaseDirectories();
    rejectsSymlinkedOutputRoots();
    revalidatesTheProjectDirectoryBeforeExport();
    System.out.println("OutputWorkspaceTest: " + assertions + " assertions passed");
  }

  private static void createsOnlyTheConfinedWorkspace() throws Exception {
    Path base = Files.createTempDirectory("ink-engine-output-base-");
    OutputWorkspace workspace = OutputWorkspace.fromConfiguration(config(base, "ink-engine"));
    Path expected = base.toRealPath().resolve("processing/ink-engine");
    check(workspace.projectDirectory().equals(expected), "project directory must be exact");
    check(Files.isDirectory(expected), "project directory must be created");

    Path exportPath = workspace.nextExportPath();
    check(exportPath.getParent().equals(expected), "export must remain in project directory");
    check(
        exportPath.getFileName().toString().matches(
            "ink-engine-[0-9]{8}T[0-9]{6}\\.[0-9]{3}Z-[0-9a-f]{8}\\.jpg"),
        "export name must contain a UTC timestamp and collision token");
  }

  private static void rejectsInvalidConfigurationShapes() throws Exception {
    Path base = Files.createTempDirectory("ink-engine-output-shape-");
    expectFailure(() -> OutputWorkspace.fromConfiguration(null), IllegalArgumentException.class);
    expectFailure(() -> OutputWorkspace.fromConfiguration(Map.of()), IllegalArgumentException.class);
    expectFailure(
        () -> OutputWorkspace.fromConfiguration(Map.of("projects_base_dir", base.toString())),
        IllegalArgumentException.class);

    Map<String, String> extra = new HashMap<>(config(base, "ink-engine"));
    extra.put("fallback", "forbidden");
    expectFailure(() -> OutputWorkspace.fromConfiguration(extra), IllegalArgumentException.class);
  }

  private static void rejectsUnsafeAndUnknownProjectIds() throws Exception {
    Path base = Files.createTempDirectory("ink-engine-output-id-");
    String[] rejected = {"", " ", ".", "..", ".hidden", "/ink-engine", "../ink-engine",
        "ink-engine/child", "ink-engine\\child", "other-project"};
    for (String projectId : rejected) {
      expectFailure(
          () -> OutputWorkspace.fromConfiguration(config(base, projectId)),
          IllegalArgumentException.class);
    }
    check(Files.notExists(base.resolve("processing")), "invalid project ids must create no directories");
  }

  private static void rejectsUnavailableBaseDirectories() throws Exception {
    expectFailure(
        () -> OutputWorkspace.fromConfiguration(
            Map.of("projects_base_dir", "", "project_id", "ink-engine")),
        IllegalArgumentException.class);
    expectFailure(
        () -> OutputWorkspace.fromConfiguration(config(Path.of("relative-base"), "ink-engine")),
        IllegalArgumentException.class);

    Path missing = Path.of(System.getProperty("java.io.tmpdir"),
        "missing-ink-engine-base-" + System.nanoTime());
    expectFailure(() -> OutputWorkspace.fromConfiguration(config(missing, "ink-engine")), IOException.class);

    Path file = Files.createTempFile("ink-engine-output-file-", ".tmp");
    expectFailure(() -> OutputWorkspace.fromConfiguration(config(file, "ink-engine")), IOException.class);
  }

  private static void rejectsUnwritableBaseDirectories() throws Exception {
    Path base = Files.createTempDirectory("ink-engine-output-unwritable-");
    Set<PosixFilePermission> originalPermissions;
    try {
      originalPermissions = Files.getPosixFilePermissions(base);
    } catch (UnsupportedOperationException error) {
      System.out.println("OutputWorkspaceTest: POSIX permissions unavailable; unwritable case skipped");
      return;
    }

    Set<PosixFilePermission> readOnlyPermissions = Set.of(
        PosixFilePermission.OWNER_READ,
        PosixFilePermission.OWNER_EXECUTE);
    Files.setPosixFilePermissions(base, readOnlyPermissions);
    try {
      if (Files.isWritable(base)) {
        System.out.println("OutputWorkspaceTest: writable override active; unwritable case skipped");
        return;
      }
      expectFailure(
          () -> OutputWorkspace.fromConfiguration(config(base, "ink-engine")),
          IOException.class);
    } finally {
      Files.setPosixFilePermissions(base, originalPermissions);
    }
  }

  private static void rejectsSymlinkedOutputRoots() throws Exception {
    Path base = Files.createTempDirectory("ink-engine-output-link-base-");
    Path outside = Files.createTempDirectory("ink-engine-output-link-outside-");
    try {
      Files.createSymbolicLink(base.resolve("processing"), outside);
    } catch (UnsupportedOperationException | IOException error) {
      System.out.println("OutputWorkspaceTest: symlink setup unavailable; symlink case skipped");
      return;
    }
    expectFailure(() -> OutputWorkspace.fromConfiguration(config(base, "ink-engine")), IOException.class);
  }

  private static void revalidatesTheProjectDirectoryBeforeExport() throws Exception {
    Path base = Files.createTempDirectory("ink-engine-output-revalidate-base-");
    OutputWorkspace workspace = OutputWorkspace.fromConfiguration(config(base, "ink-engine"));
    Path projectDirectory = workspace.projectDirectory();
    Path outside = Files.createTempDirectory("ink-engine-output-revalidate-outside-");
    Files.delete(projectDirectory);
    try {
      Files.createSymbolicLink(projectDirectory, outside);
    } catch (UnsupportedOperationException | IOException error) {
      System.out.println("OutputWorkspaceTest: symlink replacement unavailable; revalidation case skipped");
      return;
    }
    expectFailure(workspace::nextExportPath, IOException.class);
  }

  private static Map<String, String> config(Path base, String projectId) {
    return Map.of("projects_base_dir", base.toString(), "project_id", projectId);
  }

  private static void check(boolean condition, String message) {
    assertions++;
    if (!condition) {
      throw new AssertionError(message);
    }
  }

  private static void expectFailure(ThrowingRunnable operation, Class<? extends Throwable> type)
      throws Exception {
    assertions++;
    try {
      operation.run();
    } catch (Throwable error) {
      if (type.isInstance(error)) {
        return;
      }
      throw new AssertionError(
          "Expected " + type.getSimpleName() + " but received " + error.getClass().getSimpleName(),
          error);
    }
    throw new AssertionError("Expected " + type.getSimpleName());
  }

  private interface ThrowingRunnable {
    void run() throws Exception;
  }
}
