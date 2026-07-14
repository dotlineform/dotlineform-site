//for a droplet
class DisplayOptions {
  int center;
  int outermost;
  int maxima;
  int fillDroplet; // 1 to fill the droplet, 0 for no fill
  
  // Default constructor: initializes fields to default values (0 in this case)
  DisplayOptions() {
    // Default values:
    // center, outermost, maxima default to 0, fillDroplet defaults to 0 (no fill)
    // You can optionally set default fill value here.
    // For example, to default to fill enabled, uncomment the following:
    // this.fillDroplet = 1;
  }
  
  // Parameterized constructor remains available if needed
  DisplayOptions(int center, int outermost, int maxima, int fillDroplet) {
    this.center = center;
    this.outermost = outermost;
    this.maxima = maxima;
    this.fillDroplet = fillDroplet;
  }
}

// for createDroplets 
class DropletRanges {
  int sizeMin, sizeMax;
  int complexityMin, complexityMax;
  int spreadMin, spreadMax;
  
  // Default constructor with default ranges
  DropletRanges() {
    // Default ranges can be adjusted as desired
    sizeMin = 20;
    sizeMax = 80;
    complexityMin = 1;
    complexityMax = 100;
    spreadMin = 20;
    spreadMax = 80;
  }
  
  // Parameterized constructor if you want to specify your own ranges
  DropletRanges(int sizeMin, int sizeMax, int complexityMin, int complexityMax, int spreadMin, int spreadMax) {
    this.sizeMin = sizeMin;
    this.sizeMax = sizeMax;
    this.complexityMin = complexityMin;
    this.complexityMax = complexityMax;
    this.spreadMin = spreadMin;
    this.spreadMax = spreadMax;
  }
}

// for createDroplet 
class DropletOptions {
  PVector center;
  int size;         // percentage (1-100) for the outer ellipse size relative to the drawing area
  int complexity;   // complexity (1-100)
  int spread;       // percentage of the outer ellipse defining the inner ellipse

  // Default no-argument constructor
  DropletOptions() {
    size = 50;
    complexity = 50;
    spread = 30;
  }
  
  // Parameterized constructor
  DropletOptions(PVector center, int size, int complexity, int spread) {
    this.center = center;  //coordinates of the centre of the droplet ellipses
    this.size = size; // percentage of drawing size, 1-100)
    this.complexity = complexity; // Complexity ranges from 1 to 100
    this.spread = spread; // Spread defines the inner ellipse as % of the outer ellipse
  }
}

void createDroplets(int numDroplets, DisplayOptions displayOptions, DropletRanges dropletRanges, DrawingOptions drawingOptions) {
  // List to store successfully placed droplets
  ArrayList<DropletOptions> placedDroplets = new ArrayList<DropletOptions>();
  
  int dropletsCreated = 0;
  int maxAttempts = 1000;  // Prevent infinite loop if too many droplets
  int attempts = 0;
  
  // Compute margin values based on drawingOptions.drawingMargin percentage
  float marginX = width * drawingOptions.drawingMargin / 100.0;
  float marginY = height * drawingOptions.drawingMargin / 100.0;
  
  while(dropletsCreated < numDroplets && attempts < maxAttempts) {
    attempts++;
    
    DropletOptions dropletOptions = new DropletOptions();
    // Randomly choose parameters using the ranges from dropletRanges
    dropletOptions.size = int(random(dropletRanges.sizeMin, dropletRanges.sizeMax));
    dropletOptions.complexity = int(random(dropletRanges.complexityMin, dropletRanges.complexityMax + 1));  // +1 so max is inclusive
    dropletOptions.spread = int(random(dropletRanges.spreadMin, dropletRanges.spreadMax));
    
    // Compute scale factor and outer ellipse dimensions based on size
    float scaleFactor = dropletOptions.size / 100.0;
    float outerWidth = width * scaleFactor;
    float outerHeight = height * scaleFactor;
    // Approximate outer ellipse with a circle (radius = average of half-width and half-height)
    float dropletRadius = (outerWidth + outerHeight) / 4.0;
    
    // Randomly distribute the droplet center ensuring the droplet is fully contained within the canvas with margins.
    // The candidate center is chosen so that it's at least (margin + outerWidth/2) from the left/right
    // and (margin + outerHeight/2) from the top/bottom.
    PVector candidateCenter = new PVector(
      random(marginX + outerWidth/2, width - marginX - outerWidth/2),
      random(marginY + outerHeight/2, height - marginY - outerHeight/2)
    );
    
    // Check for overlap with previously placed droplets
    boolean overlaps = false;
    for (DropletOptions placed : placedDroplets) {
      float placedScaleFactor = placed.size / 100.0;
      float placedOuterWidth = width * placedScaleFactor;
      float placedOuterHeight = height * placedScaleFactor;
      float placedRadius = (placedOuterWidth + placedOuterHeight) / 4.0;
      
      float d = dist(candidateCenter.x, candidateCenter.y, placed.center.x, placed.center.y);
      if (d < (dropletRadius + placedRadius)) {
        overlaps = true;
        break;
      }
    }
    
    // If candidate does not overlap, add it
    if (!overlaps) {
      dropletOptions.center = candidateCenter;
      placedDroplets.add(dropletOptions);
      
      // Use the passed-in displayOptions for this droplet
      createDroplet(dropletOptions, displayOptions);
      dropletsCreated++;
    }
  }
}

void createDroplet(DropletOptions dropletOptions, DisplayOptions displayOptions) {
  // Draws a closed curve with random vertices constrained between two ellipses
  // centered at (cx, cy). This version calculates ellipse dimensions and the number
  // of vertices based on the given 'size' (percentage, 1-100), 'complexity' (1-100),
  // and 'spread' (percentage of the outer ellipse defining the inner ellipse).
  // Lower complexity produces a nearly perfect circle, while higher complexity yields more variation.

  PVector center = dropletOptions.center;
  int size = dropletOptions.size;
  int complexity = dropletOptions.complexity;
  int spread = dropletOptions.spread;

  // Extract center coordinates from the PVector
  float cx = center.x;
  float cy = center.y;
  
  // Compute the scale factor as a fraction (size is a percentage)
  float scaleFactor = size / 100.0;
  
  // Outer ellipse dimensions based on the drawing area and the scale factor.
  float outerWidth = width * scaleFactor;
  float outerHeight = height * scaleFactor;
  
  // Inner ellipse dimensions are set as a percentage of the outer ellipse dimensions using spread.
  float innerWidth = outerWidth * (spread / 100.0);
  float innerHeight = outerHeight * (spread / 100.0);
  
  // Determine the number of curve points based on complexity (mapping 1 -> 10 points, 100 -> 100 points)
  int numPoints = int(lerp(10, 100, (complexity - 1) / 99.0));
  
  // Compute semi-dimensions for inner and outer ellipses
  float a_inner = innerWidth / 2.0;
  float b_inner = innerHeight / 2.0;
  float a_outer = outerWidth / 2.0;
  float b_outer = outerHeight / 2.0;
  
  // Array to store the randomly generated points
  PVector[] points = new PVector[numPoints];
  float angleStep = TWO_PI / numPoints;
  
  // Normalize complexity to a factor between 0 (for complexity=1) and 1 (for complexity=100)
  float compFactor = (complexity - 1) / 99.0;
  
  // Generate points at evenly spaced angles with interpolation between inner and outer ellipse boundaries
  for (int i = 0; i < numPoints; i++) {
    float angle = i * angleStep;
    // Coordinates on the inner ellipse
    float x_inner = cx + cos(angle) * a_inner;
    float y_inner = cy + sin(angle) * b_inner;
    // Coordinates on the outer ellipse
    float x_outer = cx + cos(angle) * a_outer;
    float y_outer = cy + sin(angle) * b_outer;
    
    // Interpolate between inner and outer boundaries:
    // For low complexity, use 0.5 (midway) for a nearly perfect circle;
    // for high complexity, use full randomness.
    float t = lerp(0.5, random(1), compFactor);
    
    float x = lerp(x_inner, x_outer, t);
    float y = lerp(y_inner, y_outer, t);
    
    points[i] = new PVector(x, y);
  }
  
  // Draw the smooth closed curve using curveVertex
  // Set fill according to displayOptions.fillDroplet
  if (displayOptions.fillDroplet == 1) {
    fill(0);  // Use a default fill color (you can change this)
  } else {
    noFill();
  }
  stroke(0);
  beginShape();
  // Add an extra point at the beginning (last point) for smooth curve continuity
  curveVertex(points[numPoints - 1].x, points[numPoints - 1].y);
  // Add all the points
  for (int i = 0; i < numPoints; i++) {
    curveVertex(points[i].x, points[i].y);
  }
  // Repeat the first two points to properly close the curve
  curveVertex(points[0].x, points[0].y);
  curveVertex(points[1].x, points[1].y);
  endShape();
  
  // Draw markers only if display options are enabled
  if (displayOptions.maxima == 1) {
    // Identify local maxima (stationary points) in blue
    ArrayList<PVector> stationaryPoints = new ArrayList<PVector>();
    float[] distances = new float[numPoints];
    
    // Compute radial distances for each point
    for (int i = 0; i < numPoints; i++) {
      distances[i] = dist(cx, cy, points[i].x, points[i].y);
    }
    
    // Find points that are local maxima (using neighbors with wrap-around)
    for (int i = 0; i < numPoints; i++) {
      int prev = (i - 1 + numPoints) % numPoints;
      int next = (i + 1) % numPoints;
      if (distances[i] > distances[prev] && distances[i] > distances[next]) {
        stationaryPoints.add(points[i]);
      }
    }
    
    // Draw local maxima points in blue (10x10 pixels)
    fill(0, 0, 255);
    noStroke();
    for (PVector sp : stationaryPoints) {
      ellipse(sp.x, sp.y, 10, 10);
    }
  }
  
  if (displayOptions.outermost == 1) {
    // Identify the top 5 outermost points in red
    ArrayList<PVector> pointList = new ArrayList<PVector>(Arrays.asList(points));
    Collections.sort(pointList, new Comparator<PVector>() {
      public int compare(PVector p1, PVector p2) {
        float d1 = dist(cx, cy, p1.x, p1.y);
        float d2 = dist(cx, cy, p2.x, p2.y);
        return Float.compare(d2, d1);
      }
    });
    
    int outerCount = min(5, pointList.size());
    fill(255, 0, 0);
    noStroke();
    for (int i = 0; i < outerCount; i++) {
      PVector p = pointList.get(i);
      ellipse(p.x, p.y, 10, 10);
    }
  }
  
  if (displayOptions.center == 1) {
    // Draw the center with a small green circle
    fill(0, 255, 0);
    noStroke();
    ellipse(cx, cy, 10, 10);
  }
}
