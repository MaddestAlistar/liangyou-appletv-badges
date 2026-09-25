import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;

/** Execute the exported behavioral fixtures on Java Pattern, as used by NuvioTV. */
class RegexCheck {
    record Rule(String id, Pattern regex) {}
    static String decode(String s) { return new String(Base64.getDecoder().decode(s), StandardCharsets.UTF_8); }
    public static void main(String[] args) throws Exception {
        Path root=Path.of(args[0]); Map<String,List<Rule>> rules=new HashMap<>();
        for(String line:Files.readAllLines(root.resolve("regex-rules.tsv"))) {
            String[] v=line.split("\t",-1);
            rules.computeIfAbsent(v[0],x->new ArrayList<>()).add(new Rule(v[1],Pattern.compile(decode(v[2]))));
        }
        int count=0;
        for(String line:Files.readAllLines(root.resolve("regex-cases.tsv"))) {
            String[] v=line.split("\t",-1); String input=decode(v[1]); TreeSet<String> actual=new TreeSet<>();
            for(Rule r:rules.get(v[0])) if(r.regex().matcher(input).find()) actual.add(r.id());
            TreeSet<String> expected=new TreeSet<>(); if(!v[2].equals("-")) expected.addAll(Arrays.asList(v[2].split(",")));
            if(!expected.equals(actual)) throw new AssertionError(input+" expected "+expected+" actual "+actual);
            count++;
        }
        System.out.println("Java Pattern: "+count+" cases passed");
    }
}
