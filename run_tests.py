import subprocess, resource, datetime, json
from pathlib import Path

# Settings
CRITERION = "branch"
OUTPUT_VARS = "configuration_id,TARGET_CLASS,criterion,Coverage,Total_Goals,Covered_Goals,Size,Length,Total_Time"
TEST_SUBJECT_FILE = "./subjects.json"
LOGFILE = "./evo_output.log"
TIMESTAT_FILE = "./times.csv"
SEARCH_BUDGET = 60 * 5
ITERATIONS = 10
ALGORITHMS = ["DynaMOSA", "PRDynaMOSA"] # can also add "NCPRDynaMOSA"

projects = {}
with open(TEST_SUBJECT_FILE) as subject_file:
	projects = json.load(subject_file)
	classes = 0
	for project in projects:
		classes += len(projects[project]["classes"])
	print("Read {} projects with a total of {} classes loaded from file.".format(len(projects.keys()), classes))


now = datetime.datetime.now()
filepath = "./testruns/{}".format(now.strftime("%Y-%m-%d_%H-%M"))

print("Setting up directories...", flush=True)
Path(filepath).mkdir(parents=True, exist_ok=True)
with open("{}/{}".format(filepath, TIMESTAT_FILE), "a") as timefile:
	timefile.write("{},{},{},{}\n".format("project", "class", "algorithm", "time"))

for i in range(0,ITERATIONS):
	for project in projects:
		for algo in ALGORITHMS:
			for clas in projects[project]["classes"]:
				print("#{} - Running {} on Project {} class {}...".format(i, algo, project, clas), flush=True)
				with open("{}/{}".format(filepath, LOGFILE), "a") as logfile:
					logfile.write("Running {} on Project {} class {}...\n".format(algo, project, clas))
					usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
					run_config = ["java",
						"-jar", "evosuite/master/target/evosuite-master-1.0.7-SNAPSHOT.jar",
						"-target", "{}{}.jar".format(projects[project]["path"], project),
						"-projectCP", projects[project]["path"],
						"-criterion", CRITERION,
						"-generateMOSuite",
						"-class", clas,
						"-Doutput_variables={}".format(OUTPUT_VARS),
						"-Dshow_progress=false",
						"-Dconfiguration_id={}".format(algo),
						"-Dalgorithm={}".format(algo),
						"-Dsearch_budget={}".format(SEARCH_BUDGET)]
					print(" ".join(run_config), flush=True)
					subprocess.call(run_config,
						stdout=logfile, stderr=subprocess.STDOUT)
					usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
					cpu_time = usage_end.ru_utime - usage_start.ru_utime
					with open("{}/{}".format(filepath, TIMESTAT_FILE), "a") as timefile:
						timefile.write("{},{},{},{}\n".format(project,clas,algo,cpu_time))
					print("CPU Time taken: {}".format(cpu_time), flush=True)

print("Done!")
