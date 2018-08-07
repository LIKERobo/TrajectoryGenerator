r"""Database handling

Module to handle all sqlite database-connections.

Error-Handling is still on the TODO-List.

"""
import os
import numpy as np
import sqlite3 as sql

class DatabaseHandler(object):
    r"""Class with helper-functions for all database-handling.

    This class can be instantiated / copied by whatever module needs it.
    A "Singleton"-approach to avoid concurrency-issues was not chosen since
    `sqlite` can handle multiple readers and writing should not be an issue
    here.
    """

    def __init__(self, path):
        self.path = path

    def __copy__(self):
        return Database(self.path)

    def adapt_dict(self, parameters):
        for key in parameters:
            if isinstance(parameters[key],np.ndarray):
                parameters[key+"_arr"] = parameters[key].to_list()
                parameters.pop(key,0)
        return str(parameters)

    def convert_dict(self, text):
        parameters = eval(text)
        for key in parameters:
            if key.endswith("_arr"):
                parameters[key[:-4]] = np.array(parameters[key])
                parameters.pop(key,0)
        return parameters

    def adapt_array(self,array):
        return str(array.tolist())

    def convert_array(self, text):
        return np.array(eval(text))

    def get_connection(self):
        sql.register_adapter(np.ndarray, self.adapt_array)
        sql.register_converter("array", self.convert_array)
        sql.register_adapter(dict, self.adapt_dict)
        sql.register_converter("dict", self.convert_dict)
        return sql.connect(self.path, detect_types=sql.PARSE_DECLTYPES)

    def add_trace(self, x_list, y_list):
        r"""Append a complete trace to the table

        Parameters
        ----------
        x_list, y_list : *array_like*,*array_like*
            Lists or iterables containing the x- and y-Positions of a trace.

        """
        try:
            assert len(x_list) == len(y_list)
            for x,y in zip(x_list, y_list):
                self.add_trace_single(x,y)
        except AssertionError:
            print("Trace-Lengths don't match...")
            #do_something()

    def add_trace_single(self, x, y=None):
        if isinstance(x, np.ndarray) and y == None:
            y = x[:,1]
            x = x[:,0]
        try:
            x = int(x)
            y = int(y)
            with self.get_connection() as con:
                cur = con.cursor()
                cur.execute("INSERT INTO Trace VALUES(?,?)",(x,y))
        except ValueError:
            print("Could not convert x/y to integers: ",x,"/",y)
            #do_something()

    def dump_trace(self, xy=False):
        with self.get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT * from Trace")
            data = np.array(cur.fetchall())
            if xy:
                return data[:,0], data[:,1]
            else:
                return data

    def clear_trace(self):
        with self.get_connection() as con:
            cur = con.cursor()
            cur.executescript("""
            DROP TABLE IF EXISTS Trace;
            CREATE TABLE Trace(id INT, x INT, y INT);
            """)



    def add_simulation(self, parameters):
        valid, msg = self.validate_sim_parameters(parameters)
        if valid:
            trace = parameters["trace"]
            length = parameters["length"]
            map_path = parameters["map"]
            n_runs = parameters["n_runs"]
            sigma_pre = parameters["sigma_pre"]
            sigma_post = parameters["sigma_post"]
            sim_type = parameters["type"]
            specific = parameters["specific"]

            with self.get_connection() as con:
                cur = con.cursor()
                cur.execute("INSERT INTO Simulation VALUES(?,?,?,?,?,?,?,?)",\
                            (trace,length,map_path,n_runs,sigma_pre,sigma_post,\
                             sim_type,specific))
        return valid, msg

    def validate_sim_parameters(self, parameters):
        #Check if all parameters are there.
        valid_keys = ["trace", "length", "map", "n_runs", "sigma_pre","sigma_post",\
                "type", "specific"]
        if not all (key in parameters.keys() for key in valid_keys):
            return False, "Not all parameters supplied."

        #Check if trace can be converted to a valid array
        trace = np.array(parameters["trace"])
        if len(trace.shape) != 2 or (trace.dtype == float and trace.dtype != int):
            return False, "Could not convert Trace to valid array."

        #Greater than zero
        def gtz(name):
            if float(parameters[name]) <= 0:
                raise ValueError("%s must be > 0"%name)
        #Check if parameters can be converted to integers/floats
        try:
            gtz("length")
            gtz("n_runs")
            gtz("sigma_pre")
            gtz("sigma_post")
        except ValueError as e:
            return False, str(e)

        if not os.path.exists(parameters["map"]):
            return False, "map-path is not valid."

        return True, ""


    def renumber_trace(self):
        #Next Index
        cur.execute("SELECT MAX(id) from Trace")
        next_index = cur.fetchone()[0]
        #Total Nr of rows
        cur.execute("SELECT Count(*) from Trace")
        total = cur.fetchone()[0]
        if next_index+1 != total:
            cur.execute("SELECT id from Trace")
            old_id = cur.fetchall()
            for i in range(total):
                cur.execute("UPDATE Trace SET id=? WHERE id=?",(i,old_id[i][0]))


    def create_empty_database(self):
        try:
            with self.get_connection() as con:
                cur = con.cursor()
                cur.executescript("""
                DROP TABLE IF EXISTS Trace;
                DROP TABLE IF EXISTS Simulation;
                CREATE TABLE Trace(id INT, x INT, y INT);
                CREATE TABLE Simulation(trace array, length INT,
                                        map TEXT, n_runs INT,
                                        sigma_pre FLOAT, sigma_post FLOAT,
                                        type TEXT, specific dict);
                """)
                # DROP TABLE IF EXISTS Settings;
                # CREATE TABLE GuiSettings(export_size TEXT, value TEXT);
        except sql.Error as e:
            if con:
                con.rollback()
            print("SQL-Error: ",e)




    def create_test_input(self):
        self.create_empty_database()

        x = [1,2,3,4,5]
        y = [11,22,33,44,55]

        self.add_trace(x,y)

        m = np.array([x,y])
        sim = {"trace":m,\
               "length": 100,\
               "map": "../maps/empty_1200x1200.png",\
               "n_runs": 5,\
               "sigma_pre": 0.5,\
               "sigma_post": 5.0,\
               "type": "interpolation",\
               "specific": {"kind":"cubic"}}
        self.add_simulation(sim)


if __name__ == "__main__":
    path = ".tmp.db"
    DB = DatabaseHandler(path)
    DB.create_test_input()
    x = DB.read_trace()
    print(x)
    print(type(x))
