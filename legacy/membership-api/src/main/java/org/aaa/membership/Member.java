package org.aaa.membership;

import java.math.BigDecimal;
import java.util.Date;

public class Member {
    final String id, name, phone, plan, status;
    final Date expires;
    final BigDecimal paid;

    Member(String id, String name, String phone, String plan, String status, Date expires, BigDecimal paid) {
        this.id = id; this.name = name; this.phone = phone; this.plan = plan;
        this.status = status; this.expires = expires; this.paid = paid;
    }
}
