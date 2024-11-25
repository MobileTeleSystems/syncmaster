/*

Enter custom T-SQL here that would run after SQL Server has started up.

*/

CREATE DATABASE syncmaster;
GO

USE syncmaster;
GO

CREATE LOGIN syncmaster WITH PASSWORD = '7ellowEl7akey';
GO

CREATE USER syncmaster FOR LOGIN syncmaster;
GO

GRANT CONTROL ON DATABASE::syncmaster TO syncmaster;
GO
