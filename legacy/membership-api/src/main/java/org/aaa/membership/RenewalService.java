package org.aaa.membership;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Calendar;
import java.util.Date;
import java.util.Properties;

/** Renewals: one more year, at the plan's price, 5% off with autopay. */
public class RenewalService {

    static class Result {
        Date newExpiry;
        BigDecimal charged;
    }

    private final Properties config = Config.load();

    public Result renew(Member m, boolean autopay) {
        Calendar today = Calendar.getInstance();          // server time zone (UTC in the data centre)
        Calendar start = Calendar.getInstance();
        start.setTime(m.expires);

        int grace = Integer.parseInt(config.getProperty("renewal.grace.days"));
        Calendar graceEnd = (Calendar) start.clone();
        graceEnd.add(Calendar.DAY_OF_MONTH, grace);

        // Lapsed for longer than the grace period: the new year starts today, not at the old expiry.
        if ("LAPSED".equals(m.status) && today.after(graceEnd)) {
            start = today;
        }
        start.add(Calendar.YEAR, 1);                      // 29 Feb + 1 year = 28 Feb

        BigDecimal price = new BigDecimal(config.getProperty("price." + m.plan));
        if (autopay) {
            BigDecimal discount = new BigDecimal(config.getProperty("autopay.discount"));
            price = price.subtract(price.multiply(discount)).setScale(2, RoundingMode.HALF_UP);
        }

        Result r = new Result();
        r.newExpiry = start.getTime();
        r.charged = price;
        return r;
    }
}
