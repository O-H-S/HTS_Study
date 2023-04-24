import sqlite3
import random
import string, threading

class SQLManager:
    def __init__(self, path):
        
        
        self.cons = {}
        self.targetPath = path
        if not self.IsTableExists("Meta") :
            con = self.GetCurConnection()
            cursor = con.cursor()
            listOfTables = cursor.execute("CREATE TABLE Meta(key text PRIMARY KEY, value)")
            con.commit()
            cursor.close()
    
        
    
                
    def Close(self):
        for tid, con in self.cons.items():
            con.close()
    
    def GetCurConnection(self):
        tid = threading.get_ident() 
        if tid in self.cons:
            return self.cons[tid]
            
        newCon = sqlite3.connect(self.targetPath, check_same_thread=False)    
        self.cons[tid] = newCon
        return newCon
    
    def GetListQuery(self, targetList):
        return "({0})".format(','.join(['?']*len(targetList)))
    
    def IsTableExists(self, name):
    
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        listOfTables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{0}';".format(name)).fetchall()
        cursor.close()
        
        if len(listOfTables) == 0:
            return False
        return True
    def IsIndexExists(self, name):
    
        con = self.GetCurConnection()
        cursor = con.cursor()
        listOfTables = cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='{0}';".format(name)).fetchall()
        cursor.close()
        
        if len(listOfTables) == 0:
            return False
        return True
    def CreateTable(self, name, parameters, forQuery = False):
        if forQuery:
            return "CREATE TABLE {0}({1})".format(name, parameters)
        con = self.GetCurConnection()
        cursor = con.cursor()
        cursor.execute("CREATE TABLE {0}({1})".format(name, parameters))
        con.commit()
        cursor.close()
    
    def CreateIndex(self, name, parameters):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("CREATE INDEX {0} ON {1}".format(name, parameters))
        con.commit()
        cursor.close()
    
    
    def IsTableStructureEqual(self, targetTableName, targetQuery):
    
        if self.GetTableStructure(targetTableName) == targetQuery:
            return True
        return False
       
    def RemoveTable(self, name):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("DROP TABLE {0}".format(name))
        con.commit()
        cursor.close()
        
    def RemoveIndex(self, name):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("DROP INDEX {0}".format(name))
        
        con.commit()
        cursor.close()
        
    def ClearTable(self, name):
        con = self.GetCurConnection()
        cursor = con.cursor()
        cursor.execute("DELETE FROM {0}".format(name))
        con.commit()
        cursor.close()
    
        
        
        
    def DeleteRow(self, name, whereQuery):
        con = self.GetCurConnection()
        cursor = con.cursor()
        cursor.execute("DELETE FROM {0} WHERE {1}".format(name, whereQuery))
        con.commit()
        cursor.close()
       

 
    def GetTableStructure(self, name):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        sql = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{0}';".format(name)).fetchall()
        cursor.close()
        return sql[0][0]
    def SetTableStructure(self, name, query):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("UPDATE sqlite_master SET sql='{1}' WHERE type='table' AND name='{0}';".format(name, query))
        
        con.commit()
        cursor.close()
    
    def GetAllRowSorted(self, name, sortedName, whereQuery='1', selectQuery = '*'):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("SELECT {3} FROM {0} WHERE {1} ORDER BY {2}".format(name, whereQuery, sortedName, selectQuery))
        content = cursor.fetchall()
        cursor.close()
        return content
    
    def GetAllRow(self, name, whereQuery='1', selectQuery = '*', execArgs = None):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        if execArgs is None:
            cursor.execute("SELECT {2} FROM {0} WHERE {1}".format(name, whereQuery, selectQuery))
        else:
            cursor.execute("SELECT {2} FROM {0} WHERE {1}".format(name, whereQuery, selectQuery), execArgs)
        content = cursor.fetchall()
        cursor.close()
        return content
     
    def GetCountByGroup(self, name, groupTarget):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("SELECT {0}, COUNT(*) FROM {1} GROUP BY {0}".format(groupTarget, name))
        content = cursor.fetchall()
        cursor.close()
        return content
    
    def InsertRowList(self, name, rowList, colCount, paramQuery = None):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        formatStr = ['(?']
        for i in range(0, colCount-1):
            formatStr.append(',?')
        formatStr.append(')')

        if paramQuery is None:
            cursor.executemany("INSERT INTO {0} VALUES{1}".format(name,''.join(formatStr)), rowList)
        else:
            cursor.executemany("INSERT INTO {0}({2}) VALUES{1}".format(name,''.join(formatStr), paramQuery), rowList)
        con.commit()
        cursor.close()
    
    def ParseDataToString(self, dataList):
        results = []
        for dt in dataList:
            if type(dt) is str:
                results.append("'{0}'".format(dt))
            else:
                results.append(str(dt))
        return ','.join(results)
    
    def InsertOneRow(self, name, params, row):
    
        con = self.GetCurConnection()
        cursor = con.cursor()
        #print("INSERT INTO {0}({1}) VALUES({2})".format(name, params, ','.join(row)))
        parsed = self.ParseDataToString( row)
        cursor.execute("INSERT INTO {0}({1}) VALUES({2})".format(name, params, parsed))
        newID = cursor.lastrowid
        
        con.commit()
        cursor.close()
    
        return newID
    
    def UpsertRowList(self, target, keyName, rowList):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        colCount = len(rowList[0])
        
        
        
        
        formatStr = ['(?']
        for i in range(0, colCount-1):
            formatStr.append(',?')
        formatStr.append(')')
        
        firstBound = target.find("(")
        lastBound = target.find(")")
        target_content = target[firstBound+1: lastBound]
        #print(target_content)
        cols = target_content.split(',')
        
        doingQuery = ""
        for col in cols:
            doingQuery = doingQuery + "{0}=excluded.{0},".format(col)
        doingQuery = doingQuery[:-1]    
        #print(doingQuery)

        
        cursor.executemany("INSERT INTO {0} VALUES{1} ON CONFLICT({2}) DO UPDATE SET {3};".format(target,''.join(formatStr), keyName, doingQuery), rowList)
        newID = cursor.lastrowid
        
        con.commit()
        cursor.close()
    
        return newID
    
        '''
        INSERT INTO players (user_name, age)
        VALUES('steven', 32)
        ON CONFLICT(user_name)
        DO UPDATE SET age=excluded.age;
        '''
    
    def GetTableColumns(self, name):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        cursor.execute("PRAGMA table_info('{0}');".format(name))
        content = cursor.fetchall()
        cursor.close()
        return content
    def GetTableColumnNames(self, name):
        cols = self.GetTableColumns( name)
        names = []
        for col in cols:
            names.append(col[1])
        return names
      
    def GetMetaData(self, key):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        listOfValues = cursor.execute("SELECT value FROM Meta WHERE key='{0}';".format(key)).fetchone()
        cursor.close()
        if listOfValues == None :
            return None
        return listOfValues[0]
        
       
    def SetMetaData(self, key, value):
        con = self.GetCurConnection()
        cursor = con.cursor()
        
        found = cursor.execute("SELECT key FROM Meta WHERE key='{0}'".format(key)).fetchall()
        
        cursor2 = con.cursor()
        if len(found) == 0:
            cursor2.execute("INSERT INTO Meta VALUES('{0}', '{1}')".format(key, value))
        else:
            cursor2.execute("UPDATE Meta SET value='{0}' WHERE key='{1}'".format(value, key))
        con.commit()
        cursor.close()
        cursor2.close()
    def insert_conflict_ignore(self, df, name):
        """
        Saves dataframe to the MySQL database with 'INSERT IGNORE' query.

        First it uses pandas.to_sql to save to temporary table.
        After that it uses SQL to transfer the data to destination table, matching the columns.
        Destination table needs to exist already. 
        Final step is deleting the temporary table.
        Parameters
        ----------
        df : pd.DataFrame
            dataframe to save
        table : str
            destination table name
        """
        con = self.GetCurConnection()
        engine = con
        
        # generate random table name for concurrent writing
        temp_table = ''.join(random.choice(string.ascii_letters) for i in range(10))
        
        
        cursor = con.cursor()
        
        cursor.execute("CREATE TABLE {0} AS SELECT * FROM {1} WHERE 0 ".format(temp_table, name))
        con.commit()
        cursor.close()
        
        try:
            df.to_sql(temp_table, engine, if_exists='append', index=False)
            #columns = self.table_column_names(table=name)
            #print(column)
            #insert_query = f'INSERT IGNORE INTO {table}({columns}) SELECT {columns} FROM `{temp_table}`'
            insert_query = f'INSERT OR IGNORE INTO {name} SELECT * FROM `{temp_table}`'
            engine.execute(insert_query)
        except Exception as e:
            print(e)        

        # drop temp table
        drop_query = f'DROP TABLE IF EXISTS `{temp_table}`'
        engine.execute(drop_query)
        engine.commit()

    def table_column_names(self, table):
        """
        Get column names from database table
        Parameters
        ----------
        table : str
            name of the table
        Returns
        -------
        str
            names of columns as a string so we can interpolate into the SQL queries
        """
        con = self.GetCurConnection()
        engine = con
        query = f"SELECT column_name FROM sqlite_master WHERE name = '{table}'"
        rows = engine.execute(query)
        dirty_names = [i[0] for i in rows]
        clean_names = '`' + '`, `'.join(map(str, dirty_names)) + '`'
        return clean_names
        

    
    
    


 