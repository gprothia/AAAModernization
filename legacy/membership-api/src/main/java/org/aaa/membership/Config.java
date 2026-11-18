package org.aaa.membership;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

final class Config {
    static Properties load() {
        Properties p = new Properties();
        try (InputStream in = Config.class.getResourceAsStream("/membership.properties")) {
            p.load(in);
        } catch (IOException e) {
            throw new IllegalStateException("membership.properties missing", e);
        }
        return p;
    }
}
