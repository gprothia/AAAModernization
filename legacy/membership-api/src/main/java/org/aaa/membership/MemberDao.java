package org.aaa.membership;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Date;

/** All database access. Plain JDBC; the connection URL comes from the container. */
public class MemberDao {

    private Connection connect() throws SQLException {
        return DriverManager.getConnection(System.getProperty("membership.db", "jdbc:h2:mem:members;INIT=RUNSCRIPT FROM '/seed.sql'"));
    }

    public User login(String username, String password) {
        try (Connection c = connect();
             PreparedStatement s = c.prepareStatement("SELECT role, member_id FROM users WHERE username=? AND password=?")) {
            s.setString(1, username);
            s.setString(2, password);                    // stored and compared in clear text
            ResultSet rs = s.executeQuery();
            return rs.next() ? new User(username, rs.getString(1), rs.getString(2)) : null;
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }

    public Member find(String id) {
        try (Connection c = connect();
             PreparedStatement s = c.prepareStatement("SELECT name, phone, plan, status, expires, paid FROM members WHERE member_id=?")) {
            s.setString(1, id);
            ResultSet rs = s.executeQuery();
            if (!rs.next()) return null;
            return new Member(id, rs.getString(1), rs.getString(2), rs.getString(3), rs.getString(4),
                    rs.getDate(5), rs.getBigDecimal(6));
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }

    public void saveRenewal(String id, Date newExpiry, BigDecimal charged) {
        update("UPDATE members SET status='ACTIVE', expires=?, paid=? WHERE member_id=?", newExpiry, charged, id);
        update("INSERT INTO payments (member_id, amount, kind, at) VALUES (?, ?, 'RENEWAL', NOW())", id, charged);
    }

    public void saveCancellation(String id, int refund) {
        update("UPDATE members SET status='CANCELLED' WHERE member_id=?", id);
        update("INSERT INTO payments (member_id, amount, kind, at) VALUES (?, ?, 'REFUND', NOW())", id, -refund);
    }

    private void update(String sql, Object... args) {
        try (Connection c = connect(); PreparedStatement s = c.prepareStatement(sql)) {
            for (int i = 0; i < args.length; i++) {
                Object a = args[i];
                s.setObject(i + 1, a instanceof Date ? new java.sql.Date(((Date) a).getTime()) : a);
            }
            s.executeUpdate();
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }
}
