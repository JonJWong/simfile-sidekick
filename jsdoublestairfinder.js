const fs = require('fs');

function checkAndReplaceMine(row) {
    for (let i = 0; i < row.length; i++) {
        if (row[i] === "M") {
            row[i] = "0";
        }
    }
    return row
}

function findMeasureWithDoubleStair(dir) {
    const STEPS = {
        "1000": "L",
        "0100": "D",
        "0010": "U",
        "0001": "R",
        "2000": "L",
        "0200": "D",
        "0020": "U",
        "0002": "R",
        "4000": "L",
        "0400": "D",
        "0040": "U",
        "0004": "R"
    };

    const DIFFICULTIES = [
        "Beginner",
        "Easy",
        "Medium",
        "Hard",
        "Challenge",
        "Edit"
    ];

    const OTHER_STEPS = [
        "3000", "0300", "0030", "0003",
        "M000", "0M00", "00M0", "000M",
        "0000"
    ];

    const DBL_STAIRS = [
        "LDURLDUR",
        "LUDRLUDR",
        "RUDLRUDL",
        "RDULRDUL"
    ];

    try {
        const chart = fs.readFileSync(dir, 'utf8');
        const chartRows = chart.split("\n");

        let measure = 0;
        let currPattern = "";
        let currDifficulty = "";
        let description = "";
        let printedDiff = "";
        let chartStarted = false;

        for (let i = 0; i < chartRows.length; i++) {
            const row = chartRows[i];

            if (row.includes("DESCRIPTION")) {
                description = row.split(":")[1].slice(0, -1);
            }

            for (const difficulty of DIFFICULTIES) {
                if (row.includes(difficulty)) {
                    currDifficulty = difficulty;
                }
            }

            if (STEPS[row] || OTHER_STEPS.includes(row)) {
                chartStarted = true;
            }

            const minelessRow = checkAndReplaceMine(row);

            if (!chartStarted) {
                continue;
            }

            if (row.startsWith("//") && chartStarted) {
                measure = 0;
                currPattern = "";
                currDifficulty = "";
                description = "";
                chartStarted = false;
                continue;
            }

            if (row === ",") {
                measure++;
                continue;
            }

            if (STEPS[minelessRow]) {
                currPattern += STEPS[minelessRow];
            } else {
                if (row.includes("3") && STEPS[checkAndReplaceMine(chartRows[i - 1])] && currPattern.length > 0) {
                    continue;
                }

                currPattern = "";
            }

            if (!DBL_STAIRS.some(dblStair => currPattern.startsWith(dblStair))) {
                for (let j = 1; j < currPattern.length; j++) {
                    if (currPattern[j] === "L" || currPattern[j] === "R") {
                        currPattern = currPattern.substring(j);
                    }
                }
                continue;
            }

            if (currPattern.length === 8) {
                if (currDifficulty !== printedDiff) {
                    console.log("Difficulty: " + currDifficulty);
                    printedDiff = currDifficulty;
                }

                if (currDifficulty === "Edit") {
                    console.log("Description: " + description);
                }

                console.log(currPattern + " found ending in measure " + measure);
                currPattern = "";
            }
        }

        console.log("Finished checking for double-stairs.");
    } catch (err) {
        console.error("Error: " + err);
    }
}

const dir = "C:\\Users\\China\\OneDrive\\Desktop\\itgmania\\Songs\\Big Wong\\Russian Roulette\\russianroulette.sm";
findMeasureWithDoubleStair(dir);