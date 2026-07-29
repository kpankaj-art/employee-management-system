<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Attendance System</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f4f6f9;
      margin: 20px;
    }

    .container {
      max-width: 900px;
      margin: 0 auto;
      background: #fff;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* Controls & Selectors */
    .controls {
      display: flex;
      gap: 15px;
      margin-bottom: 20px;
      align-items: center;
      flex-wrap: wrap;
    }

    .controls select, .controls input {
      padding: 8px 12px;
      font-size: 14px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }

    /* Summary Bar */
    .summary-bar {
      display: flex;
      justify-content: space-around;
      background-color: #eef2f5;
      padding: 15px;
      border-radius: 6px;
      margin-bottom: 20px;
      font-weight: bold;
    }

    .summary-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
    }

    /* Calendar Grid */
    .calendar-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 8px;
    }

    .day-header {
      font-weight: bold;
      text-align: center;
      padding: 10px;
      background: #343a40;
      color: #fff;
      border-radius: 4px;
    }

    .day-card {
      min-height: 80px;
      border: 1px solid #ddd;
      border-radius: 6px;
      padding: 8px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      cursor: pointer;
      transition: transform 0.1s ease;
    }

    .day-card:hover {
      transform: scale(1.02);
    }

    .date-number {
      font-weight: bold;
      font-size: 14px;
    }

    .status-badge {
      font-size: 12px;
      font-weight: bold;
      color: #fff;
      padding: 4px 8px;
      border-radius: 4px;
      text-align: center;
      align-self: flex-end;
    }

    /* Status Color Codes */
    .status-P {
      background-color: #28a745 !important; /* Green */
      color: #fff;
    }

    .status-A {
      background-color: #dc3545 !important; /* Red */
      color: #fff;
    }

    .status-H {
      background-color: #fd7e14 !important; /* Orange */
      color: #fff;
    }

    .empty-card {
      background-color: transparent;
      border: none;
      cursor: default;
    }
  </style>
</head>
<body>

<div class="container">
  <h2>📅 ATTENDANCE SYSTEM</h2>

  <!-- Selection Controls -->
  <div class="controls">
    <label for="employeeSelect">Employee:</label>
    <select id="employeeSelect">
      <option value="emp1">Rahul Sharma</option>
      <option value="emp2">Priya Verma</option>
      <option value="emp3">Amit Kumar</option>
    </select>

    <label for="monthSelect">Month:</label>
    <select id="monthSelect"></select>

    <label for="yearSelect">Year:</label>
    <select id="yearSelect"></select>
  </div>

  <!-- Monthly Summary Count -->
  <div class="summary-bar">
    <div class="summary-item">🟢 Total Present: <span id="countP">0</span></div>
    <div class="summary-item">🔴 Total Absent: <span id="countA">0</span></div>
    <div class="summary-item">🟠 Total Holidays: <span id="countH">0</span></div>
  </div>

  <!-- Calendar Grid -->
  <div class="calendar-grid" id="calendarGrid"></div>
</div>

<script>
  // Global State for storing attendance
  const attendanceData = {}; 

  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Initialize Selectors
  const monthSelect = document.getElementById("monthSelect");
  const yearSelect = document.getElementById("yearSelect");
  const employeeSelect = document.getElementById("employeeSelect");

  const currentDate = new Date();
  
  months.forEach((m, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = m;
    if (i === currentDate.getMonth()) opt.selected = true;
    monthSelect.appendChild(opt);
  });

  const currentYear = currentDate.getFullYear();
  for (let y = currentYear - 2; y <= currentYear + 2; y++) {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    if (y === currentYear) opt.selected = true;
    yearSelect.appendChild(opt);
  }

  // Event Listeners
  monthSelect.addEventListener("change", renderCalendar);
  yearSelect.addEventListener("change", renderCalendar);
  employeeSelect.addEventListener("change", renderCalendar);

  // Helper Function: Check if date is 2nd Saturday
  function isSecondSaturday(date) {
    if (date.getDay() !== 6) return false; // Not a Saturday
    const dayOfMonth = date.getDate();
    return dayOfMonth > 7 && dayOfMonth <= 14;
  }

  // Render Calendar Logic
  function renderCalendar() {
    const month = parseInt(monthSelect.value);
    const year = parseInt(yearSelect.value);
    const empId = employeeSelect.value;

    const grid = document.getElementById("calendarGrid");
    grid.innerHTML = "";

    // Header Row (Sun-Sat)
    daysOfWeek.forEach(day => {
      const header = document.createElement("div");
      header.className = "day-header";
      header.textContent = day;
      grid.appendChild(header);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const totalDays = new Date(year, month + 1, 0).getDate();

    // Empty Slots before Day 1
    for (let i = 0; i < firstDay; i++) {
      const emptyCard = document.createElement("div");
      emptyCard.className = "day-card empty-card";
      grid.appendChild(emptyCard);
    }

    let pCount = 0, aCount = 0, hCount = 0;

    // Render Days of Month
    for (let day = 1; day <= totalDays; day++) {
      const dateObj = new Date(year, month, day);
      const dateKey = `${empId}_${year}_${month}_${day}`;
      const dayOfWeek = dateObj.getDay();

      // Default Status Rule: Sunday & 2nd Saturday are Holiday (H), others Present (P)
      let status = "P";
      if (dayOfWeek === 0 || isSecondSaturday(dateObj)) {
        status = "H";
      }

      // If user manually changed status previously, override default
      if (attendanceData[dateKey]) {
        status = attendanceData[dateKey];
      } else {
        attendanceData[dateKey] = status;
      }

      // Count summary
      if (status === "P") pCount++;
      if (status === "A") aCount++;
      if (status === "H") hCount++;

      // Create Day Card Element
      const card = document.createElement("div");
      card.className = `day-card status-${status}`;
      
      const dateNum = document.createElement("div");
      dateNum.className = "date-number";
      dateNum.textContent = day;

      const badge = document.createElement("div");
      badge.className = "status-badge";
      badge.textContent = status === "P" ? "P (Present)" : status === "A" ? "A (Absent)" : "H (Holiday)";

      card.appendChild(dateNum);
      card.appendChild(badge);

      // Click event to toggle status: P -> A -> H -> P
      card.addEventListener("click", () => {
        if (attendanceData[dateKey] === "P") {
          attendanceData[dateKey] = "A";
        } else if (attendanceData[dateKey] === "A") {
          attendanceData[dateKey] = "H";
        } else {
          attendanceData[dateKey] = "P";
        }
        renderCalendar(); // Re-render to update UI and Counts
      });

      grid.appendChild(card);
    }

    // Update Summary UI
    document.getElementById("countP").textContent = pCount;
    document.getElementById("countA").textContent = aCount;
    document.getElementById("countH").textContent = hCount;
  }

  // Initial Run
  renderCalendar();
</script>

</body>
</html>
