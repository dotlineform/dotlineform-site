import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

final class OutputWorkspace {
  private static final String EXPECTED_PROJECT_ID = "ink-engine";
  private static final Set<String> CONFIG_KEYS = Set.of("projects_base_dir", "project_id");
  private static final DateTimeFormatter EXPORT_TIMESTAMP =
      DateTimeFormatter.ofPattern("uuuuMMdd'T'HHmmss.SSS'Z'").withZone(ZoneOffset.UTC);

  private final Path projectsBaseDirectory;
  private final Path projectDirectory;

  private OutputWorkspace(Path projectsBaseDirectory, Path projectDirectory) {
    this.projectsBaseDirectory = projectsBaseDirectory;
    this.projectDirectory = projectDirectory;
  }

  static OutputWorkspace fromConfiguration(Map<String, String> configuration) throws IOException {
    if (configuration == null || !configuration.keySet().equals(CONFIG_KEYS)) {
      throw new IllegalArgumentException(
          "Output configuration must contain exactly projects_base_dir and project_id.");
    }

    String rawBaseDirectory = configuration.get("projects_base_dir");
    String projectId = configuration.get("project_id");
    validateProjectId(projectId);

    if (rawBaseDirectory == null || rawBaseDirectory.isBlank()) {
      throw new IllegalArgumentException("projects_base_dir must not be blank.");
    }

    Path configuredBase = Paths.get(rawBaseDirectory);
    if (!configuredBase.isAbsolute()) {
      throw new IllegalArgumentException("projects_base_dir must be an absolute path.");
    }

    Path realBase = configuredBase.toRealPath();
    requireUsableDirectory(realBase, "projects_base_dir");

    Path processingDirectory = confinedChild(realBase, "processing");
    ensurePlainDirectory(processingDirectory, realBase, "Processing output root");

    Path projectDirectory = confinedChild(processingDirectory, projectId);
    ensurePlainDirectory(projectDirectory, realBase, "Processing project directory");
    requireUsableDirectory(projectDirectory, "Processing project directory");

    return new OutputWorkspace(realBase, projectDirectory.toRealPath());
  }

  Path projectDirectory() {
    return projectDirectory;
  }

  Path nextExportPath() throws IOException {
    verifyProjectDirectory();
    String timestamp = EXPORT_TIMESTAMP.format(Instant.now());
    String collisionToken = UUID.randomUUID().toString().substring(0, 8);
    Path exportPath = projectDirectory.resolve(
        "ink-engine-" + timestamp + "-" + collisionToken + ".jpg").normalize();
    if (!exportPath.getParent().equals(projectDirectory)) {
      throw new IOException("Export filename escaped the configured project directory.");
    }
    return exportPath;
  }

  private void verifyProjectDirectory() throws IOException {
    if (Files.isSymbolicLink(projectDirectory)) {
      throw new IOException("Processing project directory must not be a symbolic link.");
    }
    Path currentProjectDirectory = projectDirectory.toRealPath(LinkOption.NOFOLLOW_LINKS);
    if (!currentProjectDirectory.equals(projectDirectory)
        || !currentProjectDirectory.startsWith(projectsBaseDirectory)) {
      throw new IOException("Processing project directory no longer resolves inside projects_base_dir.");
    }
    requireUsableDirectory(currentProjectDirectory, "Processing project directory");
  }

  private static void validateProjectId(String projectId) {
    if (projectId == null || projectId.isBlank()) {
      throw new IllegalArgumentException("project_id must not be blank.");
    }
    Path projectPath = Paths.get(projectId);
    if (projectPath.isAbsolute()
        || projectPath.getNameCount() != 1
        || projectId.equals(".")
        || projectId.equals("..")
        || projectId.startsWith(".")
        || projectId.contains("/")
        || projectId.contains("\\")) {
      throw new IllegalArgumentException("project_id must be one visible relative path segment.");
    }
    if (!projectId.equals(EXPECTED_PROJECT_ID)) {
      throw new IllegalArgumentException("Unknown InkEngine project_id: " + projectId);
    }
  }

  private static Path confinedChild(Path parent, String child) throws IOException {
    Path candidate = parent.resolve(child).normalize();
    if (!candidate.startsWith(parent)) {
      throw new IOException("Configured output path escapes projects_base_dir.");
    }
    return candidate;
  }

  private static void ensurePlainDirectory(Path directory, Path realBase, String label)
      throws IOException {
    if (Files.exists(directory, LinkOption.NOFOLLOW_LINKS)) {
      if (Files.isSymbolicLink(directory)) {
        throw new IOException(label + " must not be a symbolic link: " + directory);
      }
      if (!Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)) {
        throw new IOException(label + " is not a directory: " + directory);
      }
    } else {
      Files.createDirectory(directory);
    }

    Path realDirectory = directory.toRealPath(LinkOption.NOFOLLOW_LINKS);
    if (!realDirectory.startsWith(realBase)) {
      throw new IOException(label + " escapes projects_base_dir: " + directory);
    }
  }

  private static void requireUsableDirectory(Path directory, String label) throws IOException {
    if (!Files.isDirectory(directory)
        || !Files.isReadable(directory)
        || !Files.isWritable(directory)) {
      throw new IOException(label + " must be an existing readable and writable directory: " + directory);
    }
  }
}
