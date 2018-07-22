# RoomIssue
**Phase1**: Therea are three function issue() which is called by user. issue initializes data of type List<> with size 10040. Then data is inserting in database from a background thread and after Completion of insertion, ReadAfterWrite() is called which reads the data from database. Function ReadWithWrite is just called after isertion thread is started. ReadWithWrite() also tries to read data from database using a background thread. **In phase1 we do not wrap ReadWithWrite() read query inside a transaction**.
  - Code1: [ReadWithoutReadingTransaction](https://github.com/amitkvikram/RoomIssue/blob/master/readWithoutAddingTransaction).
  - Output: 
  
            07-22 23:23:49.126 V/Room:Insertion: Started
            07-22 23:23:49.131 V/Room:ReadWithWrite: Started
            07-22 23:23:49.136 V/Room:ReadWithWrite: RowsRead = 0
            07-22 23:24:01.281 V/Room:Insertion: Completed
            07-22 23:24:01.281 V/Room:ReadAfterWriting: Started
            07-22 23:24:10.506 V/Room:ReadAfterWriting: Rows Read = 100040
