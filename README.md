# RoomIssue
**Phase1**: There are three function issue() which is called by user. issue initializes data of type List<> with size 100040. Then data is inserted in database from a background thread and after Completion of insertion, ReadAfterWrite() is called which reads the data from database. Function ReadWithWrite is just called after isertion thread is started. ReadWithWrite() also tries to read data from database using a background thread. **In phase1 we do not wrap ReadWithWrite() read query(method loadAllData1) inside a transaction**.
  - Code1: [ReadWithoutWrappingInTransaction](https://github.com/amitkvikram/RoomIssue/blob/master/ReadWithWrappingInTransaction).
  - Output: 
  
            07-22 23:23:49.126 V/Room:Insertion: Started
            07-22 23:23:49.131 V/Room:ReadWithWrite: Started
            07-22 23:23:49.136 V/Room:ReadWithWrite: RowsRead = 0
            07-22 23:24:01.281 V/Room:Insertion: Completed
            07-22 23:24:01.281 V/Room:ReadAfterWriting: Started
            07-22 23:24:10.506 V/Room:ReadAfterWriting: Rows Read = 100040
            
 **Phase2**: Thre is a change compared to phase1, Inside **ReadWithWrite**, read Query(method loadAllData1) is wrapped inside a transaction.
  - Code2:[ReadWithWrappingInTransaction](https://github.com/amitkvikram/RoomIssue/blob/master/ReadWithWrappingInTransaction).
  - Output:
  
            07-22 23:39:16.391 V/Room:Insertion: Started
            07-22 23:39:16.396 V/Room:ReadWithWrite: Started
            07-22 23:39:29.031 V/Room:Insertion: Completed
            07-22 23:39:29.036 V/Room:ReadAfterWriting: Started
            07-22 23:39:38.801 V/Room:ReadWithWrite: RowsRead = 100040
            07-22 23:39:38.806 V/Room:ReadAfterWriting: Rows Read = 100040
            
            
 **Conclusion**: When we write and read from two different background thread and reading is just done after writing, we are not able to read the newly inserted data. But if we wrap the read query inside a transaction and then follow the same procedure, we are able to read the newly updated data.
