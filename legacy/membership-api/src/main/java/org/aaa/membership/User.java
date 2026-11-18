package org.aaa.membership;

public class User {
    final String name, role, memberId;

    User(String name, String role, String memberId) {
        this.name = name; this.role = role; this.memberId = memberId;
    }

    /** Agents see everyone. Members see only their own record. */
    boolean canSee(String id) {
        return "AGENT".equals(role) || (memberId != null && memberId.equals(id));
    }
}
